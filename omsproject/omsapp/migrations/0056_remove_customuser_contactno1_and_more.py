# Generated by Django 5.1.4 on 2025-07-16 18:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('omsapp', '0055_customuser_userdistrict_customuser_userdistrict1_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='contactNo1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='contactPerson1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='pinCode1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='userAddress1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='userCity1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='userDistrict1',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='userNote',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='userState1',
        ),
    ]
