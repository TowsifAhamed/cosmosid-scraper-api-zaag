from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CollectedLinksViewSet, ExportedResultsViewSet, ScrapingJobViewSet

router = DefaultRouter()
router.register(r'scraping-job', ScrapingJobViewSet, basename='scraping-job')
router.register(r'collected-links', CollectedLinksViewSet)
router.register(r'exported-results', ExportedResultsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
