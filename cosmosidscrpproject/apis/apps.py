# apps.py

from django.apps import AppConfig
import asyncio

class ApisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apis'

    # def ready(self):
    #     # Import the start_scraping function from scraper.py
    #     from .scraper import start_scraping
    #     # Run the scraping task asynchronously
    #     asyncio.run(start_scraping(get_sample_links=True, update_prev_links=False))
