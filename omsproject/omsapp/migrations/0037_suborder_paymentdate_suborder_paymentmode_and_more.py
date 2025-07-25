# Generated by Django 5.1.4 on 2025-06-10 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omsapp', '0036_customuser_deactivateremark'),
    ]

    operations = [
        migrations.AddField(
            model_name='suborder',
            name='paymentDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='suborder',
            name='paymentMode',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='suborder',
            name='paymentRefNo',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='suborder',
            name='paymentStatus',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
