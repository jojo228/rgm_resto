# Generated by Django 4.1 on 2024-10-26 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_contact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='address_type',
        ),
        migrations.AddField(
            model_name='address',
            name='ville',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
