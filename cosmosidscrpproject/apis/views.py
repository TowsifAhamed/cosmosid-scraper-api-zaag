from rest_framework import viewsets
from .models import CollectedLinks, ExportedResults
from .serializers import CollectedLinksSerializer, ExportedResultsSerializer
from rest_framework.permissions import AllowAny

class CollectedLinksViewSet(viewsets.ModelViewSet):
    queryset = CollectedLinks.objects.all()
    serializer_class = CollectedLinksSerializer
    permission_classes = [AllowAny]  # Allow access to all users

class ExportedResultsViewSet(viewsets.ModelViewSet):
    queryset = ExportedResults.objects.all()
    serializer_class = ExportedResultsSerializer
    permission_classes = [AllowAny]