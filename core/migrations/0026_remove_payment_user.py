# Generated by Django 4.1 on 2024-11-07 12:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_alter_address_whatsapp_alter_cartorder_sku'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='user',
        ),
    ]