import uuid
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import ScrapingJob, ExportedResults, CollectedLinks


class ScrapingJobTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.scraping_job = ScrapingJob.objects.create(job_id=uuid.uuid4(), status="In Progress")
        self.collected_link = CollectedLinks.objects.create(
            name="SRR17798746", 
            url="/samples/bb228d07-8e89-4fab-a742-81a046438f69", 
            folder="Urinary Tract Infection Microbiome - Neugent et al 2022 - PRJNA801448 - KEPLER"
        )
        self.exported_result = ExportedResults.objects.create(
            collected_link=self.collected_link, 
            result="Bacteria", 
            taxonomy_level="class", 
            downloaded_file="/home/tlabib/Documents/github/cosmosid-scraper-api-zaag/downloads/SRR17798746_kepler-biom_class_2024-10-20_13_52.tsv"
        )

    def test_start_scraping(self):
        url = '/apis/scraping-job/start_scraping/'  
        data = {
            'get_sample_links': False,
            'update_prev_links': False
        }
        response = self.client.post(url, data, format='json')
        print("Response 1: ", response.content)

        if response.status_code == status.HTTP_202_ACCEPTED and 'job_id' in response.data:
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('job_id', response.data)

    def test_job_status(self):
        url = f'/apis/scraping-job/job_status/?job_id={self.scraping_job.job_id}'
        response = self.client.get(url)
        print("Response 2: ", response.content)

        if response.status_code == status.HTTP_200_OK and response.data['job_id'] == str(self.scraping_job.job_id):
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_id'], str(self.scraping_job.job_id))
        self.assertEqual(response.data['status'], self.scraping_job.status)

    def test_job_status_without_job_id(self):
        url = '/apis/scraping-job/job_status/'
        response = self.client.get(url)
        print("Response 3: ", response.content)

        if response.status_code == status.HTTP_400_BAD_REQUEST and response.data['error'] == 'Job ID is required':
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Job ID is required')

    def test_job_status_not_found(self):
        non_existent_job_id = str(uuid.uuid4())
        url = f'/apis/scraping-job/job_status/?job_id={non_existent_job_id}'
        response = self.client.get(url)
        print("Response 4: ", response.content)

        if response.status_code == status.HTTP_404_NOT_FOUND and response.data['error'] == 'Job not found':
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Job not found')

    def test_get_collected_links_list(self):
        url = '/apis/collected-links/'
        response = self.client.get(url)
        print("Response 5: ", response.content)

        if response.status_code == status.HTTP_200_OK and isinstance(response.data, list):
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_collected_link_by_id(self):
        url = f'/apis/collected-links/{self.collected_link.id}/'
        response = self.client.get(url)
        print("Response 6: ", response.content)

        if response.status_code == status.HTTP_200_OK and response.data['name'] == self.collected_link.name:
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.collected_link.name)
        self.assertEqual(response.data['url'], self.collected_link.url)

    def test_get_exported_results_list(self):
        url = '/apis/exported-results/'
        response = self.client.get(url)
        print("Response 7: ", response.content)

        if response.status_code == status.HTTP_200_OK and isinstance(response.data, list):
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_exported_result_by_id(self):
        url = f'/apis/exported-results/{self.exported_result.id}/'
        response = self.client.get(url)
        print("Response 8: ", response.content)

        if response.status_code == status.HTTP_200_OK and response.data['result'] == self.exported_result.result:
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], self.exported_result.result)
        self.assertEqual(response.data['taxonomy_level'], self.exported_result.taxonomy_level)

    def test_get_tsv_content(self):
        url = f'/apis/exported-results/{self.exported_result.id}/tsv_content/'
        response = self.client.get(url)
        print("Response 9: ", response.content)

        if response.status_code == status.HTTP_200_OK and isinstance(response.json(), list):
            print("Response as expected")
        else:
            print("Unexpected response")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
