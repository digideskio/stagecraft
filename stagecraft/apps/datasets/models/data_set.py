from __future__ import unicode_literals

from collections import OrderedDict
from itertools import chain, product
import requests
from socket import gethostbyaddr, gethostbyname_ex

from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction

from django.utils.encoding import python_2_unicode_compatible

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType

from stagecraft.libs.backdrop_client import create_dataset


class DeleteNotImplementedError(NotImplementedError):
    pass


class ImmutableFieldError(ValidationError):
    pass


def filter_empty_parameters(parameter_pairs):
    """
    >>> filter_empty_parameters([['t=1', 'g=2'], [None, 'g=2'], [None, None]])
    [[u't=1', u'g=2'], [u'g=2'], []]
    """
    return [filter(None, pair) for pair in parameter_pairs]


def _get_url_fragments_for_list_view(data_set):
    data_group_key_vals = [
        None,
        'data-group={}'.format(data_set.data_group.name),
        'data_group={}'.format(data_set.data_group.name),
    ]
    data_type_key_vals = [
        None,
        'data-type={}'.format(data_set.data_type.name),
        'data_type={}'.format(data_set.data_type.name),
    ]

    parameter_pairs = chain(  # permutations
        product(data_group_key_vals, data_type_key_vals),
        product(data_type_key_vals, data_group_key_vals))

    filtered = filter_empty_parameters(parameter_pairs)

    query_strings = set('&'.join(pair) for pair in filtered)
    # we import here to avoid a circular import
    from stagecraft.apps.datasets.views import list as data_set_list
    base_url = urlresolvers.reverse(data_set_list)
    url_fragments = ['{}?{}'.format(base_url, qs)
                     if qs else base_url for qs in query_strings]

    return set(url_fragments)


def _get_url_fragments_for_detail_view(data_set):
    # we import here to avoid a circular import
    from stagecraft.apps.datasets.views import detail as data_set_detail
    base_url = urlresolvers.reverse(
        data_set_detail, kwargs={'name': data_set.name})
    return set([base_url])


def get_data_set_url_fragments(data_set):
    return (_get_url_fragments_for_list_view(data_set)
            | _get_url_fragments_for_detail_view(data_set))


def purge_varnish_cache(url_fragments):
    _, _, ip_addrs = gethostbyname_ex('frontend')
    frontend_host_names = [gethostbyaddr(ip_addr)[0] for ip_addr in ip_addrs]

    hosts_for_headers = settings.HOSTS_TO_PURGE

    for frontend_host_name in frontend_host_names:
        urls = ['http://{}:7999{}'.format(frontend_host_name, url_fragment)
                for url_fragment in url_fragments]

        for host_for_headers in hosts_for_headers:
            headers = {'Host': host_for_headers}

            for url in urls:
                resp = requests.request('PURGE', url, headers=headers)


@python_2_unicode_compatible
class DataSet(models.Model):
    # used in clean() below and by DataSetAdmin
    READONLY_FIELDS = set(['name', 'capped_size'])

    name = models.SlugField(max_length=200, unique=True)
    data_group = models.ForeignKey(DataGroup, on_delete=models.PROTECT)
    data_type = models.ForeignKey(DataType, on_delete=models.PROTECT)
    raw_queries_allowed = models.BooleanField(default=True)
    bearer_token = models.CharField(max_length=255, blank=True, null=False,
                                    default="")  # "" = invalid token
    upload_format = models.CharField(max_length=255, blank=True)
    upload_filters = models.TextField(blank=True)  # a comma delimited list
    auto_ids = models.TextField(blank=True)  # a comma delimited list
    queryable = models.BooleanField(default=True)
    realtime = models.BooleanField(default=False)
    capped_size = models.PositiveIntegerField(null=True, blank=True,
                                              default=None)
    max_age_expected = models.PositiveIntegerField(null=True, blank=True,
                                                   default=60 * 60 * 24)

    def __str__(self):
        return "DataSet({})".format(self.name)

    def serialize(self):
        token_or_null = self.bearer_token if self.bearer_token != '' else None

        return OrderedDict([
            ('name',                self.name),
            ('data_group',          self.data_group.name),
            ('data_type',           self.data_type.name),
            ('raw_queries_allowed', self.raw_queries_allowed),
            ('bearer_token',        token_or_null),
            ('upload_format',       self.upload_format),
            ('upload_filters',      self.upload_filters),
            ('auto_ids',            self.auto_ids),
            ('queryable',           self.queryable),
            ('realtime',            self.realtime),
            ('capped_size',         self.capped_size),
            ('max_age_expected',    self.max_age_expected),
        ])

    def clean(self, *args, **kwargs):
        """
        Part of the interface used by the Admin UI to validate fields - see
        the docs for calling function full_clean()

        We define our own validation in here to ensure that fields we consider
        "read only" can only be set (on creation)

        Raise a ImmutableFieldError if a read only field has been modified.
        """
        super(DataSet, self).clean(*args, **kwargs)

        existing = self._get_existing()

        if existing is not None:
            previous_values = {k: existing.__dict__[k]
                               for k in self.READONLY_FIELDS}
            bad_fields = [v for v in self.READONLY_FIELDS
                          if previous_values[v] != getattr(self, v)]

            if len(bad_fields) > 0:
                bad_fields_csv = ', '.join(bad_fields)
                raise ImmutableFieldError('{} cannot be modified'
                                          .format(bad_fields_csv))

    def _get_existing(self):
        if self.pk is not None:
            return DataSet.objects.get(pk=self.pk)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.clean()
        is_insert = self.pk is None
        super(DataSet, self).save(*args, **kwargs)
        size_bytes = self.capped_size if self.is_capped else 0

        # Backdrop can't be rolled back dude.
        # Ensure this is the final action of the save method.
        if is_insert:
            create_dataset(self.name, size_bytes)
        else:
            purge_varnish_cache(get_data_set_url_fragments(self))

    @property
    def is_capped(self):
        # Actually mongo's limit for cap size minimum is currently 4096 :-(
        return (self.capped_size is not None
                and self.capped_size > 0)

    def delete(self, *args, **kwargs):
        # TODO: remember to purge the Varnish cache when we implement this
        #purge_varnish_cache(get_data_set_url_fragments(self))
        raise DeleteNotImplementedError("Data Sets cannot be deleted")

    class Meta:
        app_label = 'datasets'
        unique_together = ['data_group', 'data_type']
