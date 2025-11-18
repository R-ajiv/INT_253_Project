from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import SentimentAnalysisResult


class SentimentApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.client = APIClient()
        self.client.login(username='tester', password='pass1234')

    def test_health(self):
        url = reverse('sentiment-health')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('model', res.data)

    def test_text_analysis_returns_expected_labels(self):
        url = reverse('sentiment-analyze-text')
        res = self.client.post(url, {'transcript': 'I am happy with the support.'}, format='json')
        self.assertEqual(res.status_code, 200)
        summary = res.data.get('summary') or res.data
        self.assertIn(summary['label'], {'positive', 'negative', 'mixed', 'neutral'})
        self.assertEqual(SentimentAnalysisResult.objects.filter(user=self.user).count(), 1)

    def test_login_required_redirects(self):
        client = APIClient()
        url = reverse('sentiment-health')
        res = client.get(url)
        self.assertEqual(res.status_code, 403)

from django.test import TestCase

# Create your tests here.
