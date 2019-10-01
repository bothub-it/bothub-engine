# Generated by Django 2.1.11 on 2019-10-01 19:26

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0035_auto_20190902_1455'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionsCode',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='UUID')),
                ('codename', models.TextField(verbose_name='CodeName')),
                ('name', models.TextField(null=True, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'permissions code',
            },
        ),
        migrations.CreateModel(
            name='UserGroupRepository',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='UUID')),
                ('name', models.TextField(verbose_name='Group Name')),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Repository')),
            ],
            options={
                'verbose_name': 'User Group Repository',
            },
        ),
        migrations.CreateModel(
            name='UserPermissionRepository',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='UUID')),
                ('codename', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.PermissionsCode')),
                ('usergrouprepository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.UserGroupRepository')),
            ],
            options={
                'verbose_name': 'repository user authorization',
            },
        ),
        migrations.AddField(
            model_name='repositoryauthorization',
            name='usergrouprepository',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='common.UserGroupRepository'),
        ),
    ]
