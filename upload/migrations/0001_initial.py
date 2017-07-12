# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BigFile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('ready', models.BooleanField(default=False)),
                ('start_time', models.DateTimeField(auto_now=True)),
                ('stop_time', models.DateTimeField(null=True, default=None)),
                ('result', models.IntegerField(default=0)),
            ],
        ),
    ]
