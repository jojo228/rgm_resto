# Generated by Django 4.1 on 2024-10-02 15:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_catalogue_prix'),
    ]

    operations = [
        migrations.RenameField(
            model_name='catalogue',
            old_name='prix',
            new_name='price',
        ),
    ]
