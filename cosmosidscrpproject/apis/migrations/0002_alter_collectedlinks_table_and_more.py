# Generated by Django 4.2.13 on 2024-10-23 04:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='collectedlinks',
            table='collected_links',
        ),
        migrations.AlterModelTable(
            name='exportedresults',
            table='exported_results',
        ),
    ]
