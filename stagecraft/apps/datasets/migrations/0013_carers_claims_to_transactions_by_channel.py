# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(DataMigration):

    transaction_by_channel_data_set_mappings = [
            {
                'old_name': "carers_allowance_weekly_claims",
                'new_data_set': {
                        'auto_ids': '_timestamp,channel',
                        'date_group': "carers-allowance",
                        'date_type': "transactions-by-channel"
                    },
                #question - should also change values? cliff is finding out
                'data_mapping': {
                        'key_mapping': {
                                "key": "channel",
                                "value": "count"
                            },
                        'value_mapping': {
                            }
                    }
            }
        ]


    def forwards(self, orm):
        #non destructive - the old ones hang around in case there is a problem
        #and we need to roll back.
        for mapping in transaction_by_channel_data_set_mappings:
            migrate_data_set(mapping['old_name'], mapping['new_data_set'], mapping["data_mapping"])

    def backwards(self, orm):
        for mapping in transaction_by_channel_data_set_mappings:
            orm['datasets.DataSet'].objects.get(
                data_group=mapping['new_data_set']['data_group'],
                data_type=mapping['new_data_set']['data_type']
            ).delete()

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
                'django.db.models.fields.related.ForeignKey',
                [],
                {
                    'to': u"orm['datasets.DataGroup']",
                    'on_delete': 'models.PROTECT'
                }
            ),
            'data_type': (
                'django.db.models.fields.related.ForeignKey',
                [],
                {
                    'to': u"orm['datasets.DataType']",
                    'on_delete': 'models.PROTECT'
                }
            ),
            u'id': ('django.db.models.fields.AutoField', [], {
                'primary_key': 'True'
            }),
            'max_age_expected': (
                'django.db.models.fields.PositiveIntegerField',
                [],
                {
                    'default': '86400',
                    'null': 'True',
                    'blank': 'True'

                }
            ),
            'modified': ('django.db.models.fields.DateTimeField', [],
                         {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '200'}),
            'published': ('django.db.models.fields.BooleanField', [],
                          {'default': 'False'}),
            'queryable': ('django.db.models.fields.BooleanField', [],
                          {'default': 'True'}),
            'raw_queries_allowed': ('django.db.models.fields.BooleanField', [],
                                    {'default': 'True'}),
            'realtime': ('django.db.models.fields.BooleanField', [],
                         {'default': 'False'}),
            'upload_filters': ('django.db.models.fields.TextField', [],
                               {'blank': 'True'}),
            'upload_format': ('django.db.models.fields.CharField', [],
                              {'max_length': '255', 'blank': 'True'})
        },
        u'datasets.datatype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataType'},
            'description': ('django.db.models.fields.TextField', [],
                            {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [],
                    {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['datasets']
    symmetrical = True
