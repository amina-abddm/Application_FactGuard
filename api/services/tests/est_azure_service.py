from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.services.azure_openai_service import AzureOpenAIService

class AzureOpenAIServiceTest(TestCase):
    
    @patch.dict('os.environ', {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'os.getenv('AZURE_SEARCH_ADMIN_KEY')',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4o'
    })
    def test_service_initialization(self):
        service = AzureOpenAIService()
        self.assertTrue(service.is_available())
    
    @patch('api.services.azure_openai_service.AzureOpenAI')
    def test_analyze_content(self, mock_azure_openai):
        # Mock de la réponse Azure
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test result"
        mock_azure_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = AzureOpenAIService()
        result = service.analyze_content("Test content")
        
        self.assertEqual(result, "Test result")
