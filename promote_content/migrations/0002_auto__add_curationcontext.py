# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CurationContext'
        db.create_table('promote_content_curationcontext', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('curation', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['promote_content.Curation'], unique=True)),
            ('context_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='context_type', to=orm['contenttypes.ContentType'])),
            ('context_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='content_type', to=orm['contenttypes.ContentType'])),
            ('content_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('promote_content', ['CurationContext'])


    def backwards(self, orm):
        # Deleting model 'CurationContext'
        db.delete_table('promote_content_curationcontext')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'promote_content.curation': {
            'Meta': {'object_name': 'Curation'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'promote_content.curationcontext': {
            'Meta': {'object_name': 'CurationContext'},
            'content_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type'", 'to': "orm['contenttypes.ContentType']"}),
            'context_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'context_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'context_type'", 'to': "orm['contenttypes.ContentType']"}),
            'curation': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['promote_content.Curation']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['promote_content']