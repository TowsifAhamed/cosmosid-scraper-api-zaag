from django.db import models

class ScrapingJob(models.Model):
    job_id = models.CharField(max_length=255, primary_key=True)
    status = models.CharField(max_length=50, default="In Progress")  # Track job status ('In Progress', 'Completed')
    start_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.job_id} - {self.status}"

    class Meta:
        db_table = 'scraping_job'

class CollectedLinks(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    url = models.URLField(unique=True)
    folder = models.TextField(null=True, blank=True)
    job_id = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name="collected_links", null=True, blank=True)  # Link to scraping job
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'collected_links'

class ExportedResults(models.Model):
    collected_link = models.ForeignKey(CollectedLinks, on_delete=models.CASCADE)
    url = models.URLField(unique=True)
    result = models.TextField()
    taxonomy_level = models.TextField(null=True, blank=True)
    downloaded_file = models.TextField(null=True, blank=True)
    job_id = models.ForeignKey(ScrapingJob, on_delete=models.CASCADE, related_name="exported_results", null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('collected_link', 'result', 'taxonomy_level')
        db_table = 'exported_results'

    def __str__(self):
        return f'{self.collected_link} - {self.result}'
