# Generated by Django 2.0 on 2018-04-23 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cooggerapp', '0010_auto_20180418_2034'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otherinformationofusers',
            name='follower_count',
        ),
        migrations.RemoveField(
            model_name='otherinformationofusers',
            name='following_count',
        ),
        migrations.AlterField(
            model_name='content',
            name='cooggerup',
            field=models.BooleanField(default=False, verbose_name='was voting done'),
        ),
        migrations.AlterField(
            model_name='content',
            name='modcomment',
            field=models.BooleanField(default=False, verbose_name='was it comment by mod'),
        ),
        migrations.AlterField(
            model_name='content',
            name='upvote',
            field=models.BooleanField(default=False, verbose_name='upvote with cooggerup'),
        ),
    ]
