# Generated by Django 2.2.16 on 2020-09-18 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("common", "0088_fix_translations")]

    operations = [
        migrations.RemoveField(model_name="repository", name="allow_search_examples")
    ]