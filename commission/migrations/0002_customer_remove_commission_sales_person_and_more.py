# Generated by Django 4.1 on 2024-08-13 12:56

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commission', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referral_id', models.CharField(max_length=10, unique=True)),
                ('referred_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='commission.customer')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='commission',
            name='sales_person',
        ),
        migrations.RemoveField(
            model_name='sale',
            name='sales_person',
        ),
        migrations.AddField(
            model_name='sale',
            name='commission_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.05'), max_digits=5),
        ),
        migrations.DeleteModel(
            name='SalesPerson',
        ),
        migrations.AddField(
            model_name='commission',
            name='customer',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='commission.customer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sale',
            name='customer',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='commission.customer'),
            preserve_default=False,
        ),
    ]
