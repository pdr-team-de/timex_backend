# Generated by Django 5.1.7 on 2025-03-31 10:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_tracking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zeitarbeitsfirma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('contact_person', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='zeitarbeitsfirma',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='time_tracking.zeitarbeitsfirma'),
        ),
    ]
