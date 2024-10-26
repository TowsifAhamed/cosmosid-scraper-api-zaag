import uuid
import csv
import os
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import CollectedLinks, ExportedResults, ScrapingJob
from .serializers import CollectedLinksSerializer, ExportedResultsSerializer, StartScrapingSerializer, ScrapingJobSerializer
from .scraper import start_scraping  # Import the scraping function
from asgiref.sync import async_to_sync
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# ViewSet to manage collected links
class CollectedLinksViewSet(viewsets.ModelViewSet):
    queryset = CollectedLinks.objects.all()
    serializer_class = CollectedLinksSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['job_id', 'last_updated']

# ViewSet to manage scraping jobs
class ScrapingJobViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        method='post',
        request_body=StartScrapingSerializer,
        responses={
            202: openapi.Response('Scraping job started', ScrapingJobSerializer),
            400: 'Bad Request'
        }
    )
    @action(detail=False, methods=['post'])
    def start_scraping(self, request):
        # Use the custom serializer to validate the request data
        serializer = StartScrapingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated parameters
        get_sample_links = serializer.validated_data.get('get_sample_links', False)
        update_prev_links = serializer.validated_data.get('update_prev_links', False)

        # Generate a unique job ID
        job_id = str(uuid.uuid4())

        # Create a job entry in the database (to track the job status)
        ScrapingJob.objects.create(
            job_id=job_id,
            status="In Progress"
        )

        # Start the scraping task asynchronously with the generated job ID
        async_to_sync(start_scraping)(get_sample_links, update_prev_links, job_id)

        return Response({'status': 'Scraping started', 'job_id': job_id}, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'job_id', openapi.IN_QUERY, description="Job ID to check status", type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Response('Job status', ScrapingJobSerializer),
            400: 'Job ID is required',
            404: 'Job not found'
        }
    )
    @action(detail=False, methods=['get'])
    def job_status(self, request):
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response({'error': 'Job ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if job exists and get its status
        try:
            job = ScrapingJob.objects.get(job_id=job_id)
            return Response({'job_id': job_id, 'status': job.status})
        except ScrapingJob.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

# ViewSet to manage exported results
class ExportedResultsViewSet(viewsets.ModelViewSet):
    queryset = ExportedResults.objects.all()
    serializer_class = ExportedResultsSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['collected_link__job_id', 'taxonomy_level', 'last_updated']

    @swagger_auto_schema(
        method='get',
        responses={
            200: 'TSV file content',
            404: 'File not found',
            500: 'Internal server error'
        }
    )
    @action(detail=True, methods=['get'])
    def tsv_content(self, request, pk=None):
        try:
            exported_result = self.get_object()
            file_path = exported_result.downloaded_file

            if not file_path or not os.path.exists(file_path):
                return Response({'error': 'File not found'}, status=404)

            # Read the TSV file synchronously
            with open(file_path, mode='r') as tsv_file:
                reader = csv.DictReader(tsv_file, delimiter='\t')
                data = [row for row in reader]

            return JsonResponse(data, safe=False)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
