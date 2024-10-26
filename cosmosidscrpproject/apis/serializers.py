from rest_framework import serializers
from .models import CollectedLinks, ExportedResults, ScrapingJob

class CollectedLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectedLinks
        fields = '__all__'

class ExportedResultsSerializer(serializers.ModelSerializer):
    collected_link = CollectedLinksSerializer()  # Nested serializer to include collected link details

    class Meta:
        model = ExportedResults
        fields = '__all__'

class StartScrapingSerializer(serializers.Serializer):
    get_sample_links = serializers.BooleanField(required=False, default=False)
    update_prev_links = serializers.BooleanField(required=False, default=False)

class ScrapingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingJob
        fields = '__all__'
