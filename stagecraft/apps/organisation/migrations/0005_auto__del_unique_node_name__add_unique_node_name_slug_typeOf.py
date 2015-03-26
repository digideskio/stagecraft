# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Node', fields ['name']
        db.delete_unique(u'organisation_node', ['name'])

        # Adding unique constraint on 'Node', fields ['name', 'slug', 'typeOf']
        db.create_unique(u'organisation_node', ['name', 'slug', 'typeOf_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Node', fields ['name', 'slug', 'typeOf']
        db.delete_unique(u'organisation_node', ['name', 'slug', 'typeOf_id'])

        # Adding unique constraint on 'Node', fields ['name']
        db.create_unique(u'organisation_node', ['name'])


    models = {
        u'organisation.node': {
            'Meta': {'unique_together': "(('name', 'slug', 'typeOf'),)", 'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['organisation.Node']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '150'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['organisation']