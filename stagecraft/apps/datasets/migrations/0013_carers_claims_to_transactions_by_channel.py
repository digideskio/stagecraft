# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db.models import Q
from django.conf import settings

import pprint as pp
import json
from performanceplatform.client import DataSet as client

base_url = 'https://www.performance.service.gov.uk'

input_sets = [
    'carers_allowance_monthly_claims',
    'carers_allowance_weekly_claims'
]

output_set = 'carers_allowance_transactions_by_channel'

key_mapping = {
    "key": "channel",
    "value": "count"
}

value_mapping = {
    "ca_clerical_received": "paper",
    "ca_e_claims_received": "digital"
}


class Backdropping(object):

    def _get_output_data_set():
        data_set = client.from_name(base_url, output_set)
        data_set.set_token(settings.STAGECRAFT_COLLECTION_ENDPOINT_TOKEN)
        return data_set

    def get_data_from_claims_sets():
        input_data = []
        for set_name in input_sets:
            data_set = client.from_name(base_url, set_name)
            for item in data_set.get().json()['data']:
                input_data.append(item)
        return input_data

    def apply_new_key_mappings(document):
        for key, val in document.items():
            if key in key_mapping:
                document.pop(key)
                document[key_mapping[key]] = val
            else:
                document[key] = val
        return document

    def apply_new_values(document):
        for key, val in document.items():
            if val in value_mapping:
                document['comment'] = val
                document[key] = value_mapping[val]
        return document

    def build_documents(documents):
        docs = []
        for document in documents:
            doc = apply_new_values(apply_new_key_mappings(document))
            docs.append(doc)
        return docs

    def post_docs_to_production(documents):
        data_set = _get_output_data_set()
        data_set.post(documents)

    def clear_docs_from_output_set():
        data_set = _get_output_data_set()
        data_set.empty_data_set()


class Migration(DataMigration):

    def forwards(self, orm):
        Backdropping.post_docs_to_production(
            Backdropping.build_documents(
                Backdropping.get_data_from_claims_sets()
            )
        )

    def backwards(self, orm):
        "Write your backwards methods here."
        Backdropping.clear_docs_from_output_set()

    models = {
        u'datasets.backdropuser': {
            'Meta': {'ordering': "[u'email']", 'object_name': 'BackdropUser'},
            'data_sets': (
                'django.db.models.fields.related.ManyToManyField',
                [],
                {
                    'to': u"orm['datasets.DataSet']",
                    'symmetrical': 'False',
                    'blank': 'True'
                }
            ),
            'email': (
                'django.db.models.fields.EmailField',
                [],
                {
                    'unique': 'True',
                    'max_length': '254'
                }
            ),
            u'id': (
                'django.db.models.fields.AutoField',
                [],
                {
                    'primary_key': 'True'
                }
            )
        },
        u'datasets.datagroup': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataGroup'},
            u'id': (
                'django.db.models.fields.AutoField',
                [],
                {
                    'primary_key': 'True'
                }
            ),
            'name': (
                'django.db.models.fields.SlugField',
                [],
                {
                    'unique': 'True',
                    'max_length': '50'
                }
            )
        },
        u'datasets.dataset': {
            'Meta': {
                'ordering': "[u'name']",
                'unique_together': "([u'data_group', u'data_type'],)",
                'object_name': 'DataSet'
            },
            'auto_ids': (
                'django.db.models.fields.TextField', [], {'blank': 'True'
                }
            ),
            'bearer_token': (
                'django.db.models.fields.CharField',
                [],
                {
                    'default': "u''",
                    'max_length': '255',
                    'blank': 'True'
                }
            ),
            'capped_size': (
                'django.db.models.fields.PositiveIntegerField',
                [],
                {
                    'default': 'None',
                    'null': 'True',
                    'blank': 'True'
                }
            ),
            'created': (
                'django.db.models.fields.DateTimeField',
                [],
                {
                    'auto_now_add': 'True', 'blank': 'True'
                }
            ),
            'data_group': (
                'django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataGroup']", 'on_delete': 'models.PROTECT'
                }
            ),
            'data_type': (
                'django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataType']", 'on_delete': 'models.PROTECT'
                }
            ),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_age_expected': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'queryable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'raw_queries_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'realtime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'upload_filters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'upload_format': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'datasets.datatype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['datasets']
    symmetrical = True