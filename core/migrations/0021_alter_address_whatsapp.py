# Generated by Django 4.1 on 2024-11-04 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_address_whatsapp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='whatsapp',
            field=models.IntegerField(max_length=8),
        ),
    ]