from django.db import models

class CollectedLinks(models.Model):
    id = models.AutoField(primary_key=True)  # This should match the actual primary key in your database.
    name = models.TextField()
    url = models.URLField(unique=True)  # Make URL unique to keep it consistent.
    folder = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'collected_links'

class ExportedResults(models.Model):
    collected_link = models.ForeignKey(CollectedLinks, on_delete=models.CASCADE)
    result = models.TextField()
    taxonomy_level = models.TextField(null=True, blank=True)
    downloaded_file = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('collected_link', 'result', 'taxonomy_level')
        db_table = 'exported_results'  # Match the actual table name in your PostgreSQL database

    def __str__(self):
        return f'{self.collected_link} - {self.result}'