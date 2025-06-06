# Generated by Django 5.1.4 on 2025-05-02 09:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omsapp', '0004_alter_order_orderdate_suborder_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='userID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='orderdetails',
            name='orderID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orderdetails', to='omsapp.order'),
        ),
        migrations.AlterField(
            model_name='orderdetails',
            name='suborderID',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orderdetails', to='omsapp.suborder'),
        ),
        migrations.AlterField(
            model_name='suborder',
            name='customerID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='suborder',
            name='orderID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='omsapp.order'),
        ),
        migrations.AlterField(
            model_name='suborder',
            name='vendorID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_orders', to=settings.AUTH_USER_MODEL),
        ),
    ]
