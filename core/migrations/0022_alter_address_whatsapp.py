# Generated by Django 4.1 on 2024-11-04 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_alter_address_whatsapp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='whatsapp',
            field=models.IntegerField(),
        ),
    ]