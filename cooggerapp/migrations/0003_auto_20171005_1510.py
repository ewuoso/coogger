# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-10-05 12:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cooggerapp', '0002_blog_star'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blog',
            old_name='star',
            new_name='stars',
        ),
    ]
