# Generated by Django 4.1 on 2024-11-06 17:02

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_alter_address_whatsapp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartorder',
            name='billing_address',
        ),
        migrations.AlterField(
            model_name='cartorderproducts',
            name='image',
            field=models.ImageField(upload_to=core.models.user_directory_path),
        ),
    ]
