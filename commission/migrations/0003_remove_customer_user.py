# Generated by Django 4.1 on 2024-08-13 13:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commission', '0002_customer_remove_commission_sales_person_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='user',
        ),
    ]
