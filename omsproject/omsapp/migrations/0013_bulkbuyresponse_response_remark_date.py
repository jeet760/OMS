# Generated by Django 5.1.4 on 2025-05-09 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omsapp', '0012_alter_bulkbuyresponsedetails_bbrid'),
    ]

    operations = [
        migrations.AddField(
            model_name='bulkbuyresponse',
            name='response_remark_date',
            field=models.DateTimeField(null=True),
        ),
    ]
