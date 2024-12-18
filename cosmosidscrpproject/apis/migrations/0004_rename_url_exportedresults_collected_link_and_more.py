# Generated by Django 4.2.13 on 2024-10-23 05:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0003_collectedlinks_id_alter_collectedlinks_url'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exportedresults',
            old_name='url',
            new_name='collected_link',
        ),
        migrations.AlterUniqueTogether(
            name='exportedresults',
            unique_together={('collected_link', 'result', 'taxonomy_level')},
        ),
    ]
