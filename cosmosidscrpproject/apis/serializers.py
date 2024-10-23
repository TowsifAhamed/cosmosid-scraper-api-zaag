from rest_framework import serializers
from .models import CollectedLinks, ExportedResults

class CollectedLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectedLinks
        fields = '__all__'

class ExportedResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportedResults
        fields = '__all__'
