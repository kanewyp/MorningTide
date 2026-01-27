"""
Test suite for RAG API endpoints

Tests for therapy suggestion generation, health checks, and index management. 
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from app.main import create_app
from app.config import Config


@pytest.fixture(scope='function', autouse=True)
def mock_initialize_rag():
    """Mock RAG pipeline initialization to avoid requiring Ollama during tests"""
    with patch('app.initialize_rag_pipeline') as mock_init:
        # Create a comprehensive mock pipeline
        mock_pipeline = MagicMock()
        
        # Mock generate_suggestions
        mock_pipeline.generate_suggestions.return_value = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "diary_analysis": {
                "entry_count": 3,
                "date_range": "2026-01-21 to 2026-01-23",
                "themes": ["anxiety", "work stress", "sleep issues", "overwhelm"]
            },
            "retrieved_topics_count": 5,
            "suggestions": """DISCUSSION TOPIC 1: Managing Work-Related Anxiety

Based on your diary entries, you're experiencing significant anxiety related to work presentations.

DISCUSSION TOPIC 2: Breaking the Rumination Cycle

Your entries show a pattern of rumination - your mind keeps racing and reviewing events.

DISCUSSION TOPIC 3: Stress Management and Self-Compassion

You describe feeling "overwhelmed with everything on my plate," suggesting possible perfectionism.""",
            "model": "mistral"
        }
        
        # Mock health_check
        mock_pipeline.health_check.return_value = {
            "status": "healthy",
            "embedder": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
                "device": "cpu"
            },
            "vector_store": {
                "total_documents": 75,
                "dimension": 384,
                "store_path": "./data/vector_store"
            },
            "generator": {
                "status": "connected",
                "model": "mistral",
                "base_url": "http://localhost:11434"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock vector_store
        mock_vector_store = MagicMock()
        mock_vector_store.get_stats.return_value = {
            "total_documents": 75,
            "dimension": 384,
            "store_path": "./data/vector_store",
            "index_file_exists": True,
            "metadata_file_exists": True
        }
        mock_pipeline.vector_store = mock_vector_store
        
        # Mock retriever
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            {
                "id": "topic_001",
                "title": "Cognitive Behavioral Therapy for Anxiety",
                "similarity_score": 0.92,
                "content": "CBT techniques for managing anxiety..."
            },
            {
                "id": "topic_002",
                "title": "Sleep Hygiene and Stress Management",
                "similarity_score": 0.87,
                "content": "Improving sleep quality through stress reduction..."
            },
            {
                "id": "topic_003",
                "title": "Mindfulness for Racing Thoughts",
                "similarity_score": 0.84,
                "content": "Mindfulness techniques to calm racing thoughts..."
            }
        ]
        mock_pipeline.retriever = mock_retriever
        
        # Mock attributes
        mock_pipeline.top_k_retrieval = 5
        
        # Make initialize_rag_pipeline return the mock
        mock_init.return_value = mock_pipeline
        
        # Also patch get_rag_pipeline to return the same mock
        with patch('app.get_rag_pipeline', return_value=mock_pipeline):
            yield mock_pipeline


@pytest.fixture
def client():
    """Create Flask test client"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_diary_entries():
    """Sample diary entries for testing"""
    today = datetime.now()
    return [
        {
            "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "content": "Today I felt anxious about my work presentation. I couldn't sleep well last night."
        },
        {
            "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "content": "Had the presentation. It went okay but I'm still worried about feedback. Feeling stressed."
        },
        {
            "date": today.strftime("%Y-%m-%d"),
            "content": "Trying to relax but my mind keeps racing. I feel overwhelmed with everything on my plate."
        }
    ]


class TestGenerateSuggestions:
    """Test therapy suggestion generation endpoint"""
    
    def test_generate_suggestions_success(self, client, sample_diary_entries):
        """Test successful suggestion generation"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': sample_diary_entries,
                'top_k': 5,
                'stream': False
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert 'timestamp' in data
        assert 'diary_analysis' in data
        assert 'suggestions' in data
        assert 'model' in data
        
        # Check diary analysis
        analysis = data['diary_analysis']
        assert analysis['entry_count'] == 3
        assert 'date_range' in analysis
        assert 'themes' in analysis
        assert isinstance(analysis['themes'], list)
    
    def test_generate_suggestions_missing_field(self, client):
        """Test missing diary_entries field"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'diary_entries' in data['error'].lower()
    
    def test_generate_suggestions_empty_entries(self, client):
        """Test empty diary entries list"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': []},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_generate_suggestions_invalid_top_k(self, client, sample_diary_entries):
        """Test invalid top_k value"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': sample_diary_entries,
                'top_k': 100  # Out of range
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'top_k' in data['error'].lower()
    
    def test_generate_suggestions_invalid_json(self, client):
        """Test invalid JSON"""
        response = client.post(
            '/api/rag/generate-suggestions',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_generate_suggestions_with_custom_top_k(self, client, sample_diary_entries):
        """Test with custom top_k value"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': sample_diary_entries,
                'top_k': 3
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get('/api/rag/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'embedder' in data
        assert 'vector_store' in data
        assert 'generator' in data
        assert 'timestamp' in data
    
    def test_health_check_has_embedder_info(self, client):
        """Test that health check includes embedder info"""
        response = client.get('/api/rag/health')
        data = json.loads(response.data)
        
        embedder = data['embedder']
        assert 'model' in embedder
        assert 'dimension' in embedder
        assert 'device' in embedder
    
    def test_health_check_has_vector_store_info(self, client):
        """Test that health check includes vector store info"""
        response = client.get('/api/rag/health')
        data = json.loads(response.data)
        
        vector_store = data['vector_store']
        assert 'total_documents' in vector_store
        assert 'dimension' in vector_store
        assert 'store_path' in vector_store


class TestIndexStats:
    """Test index statistics endpoint"""
    
    def test_index_stats_success(self, client):
        """Test successful index stats retrieval"""
        response = client.get('/api/rag/index-stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'total_documents' in data
        assert isinstance(data['total_documents'], int)
        assert data['total_documents'] > 0  # Should have corpus loaded
        
        assert 'dimension' in data
        assert data['dimension'] == 384  # all-MiniLM-L6-v2 dimension
        
        assert 'store_path' in data
        assert 'index_file_exists' in data
        assert 'metadata_file_exists' in data


class TestRebuildIndex:
    """Test index rebuild endpoint"""
    
    def test_rebuild_index_success(self, client):
        """Test successful index rebuild"""
        response = client.post('/api/rag/rebuild-index')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] in ['rebuild_complete', 'rebuild_started']
        assert 'timestamp' in data
    
    def test_rebuild_index_returns_valid_json(self, client):
        """Test rebuild index returns valid JSON"""
        response = client.post('/api/rag/rebuild-index')
        
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, dict)


class TestRetrieveTopics:
    """Test topic retrieval endpoint"""
    
    def test_retrieve_topics_success(self, client):
        """Test successful topic retrieval"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={
                'query': 'I am feeling anxious about work',
                'top_k': 5
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert 'query' in data
        assert 'topics_count' in data
        assert 'topics' in data
        assert isinstance(data['topics'], list)
        assert len(data['topics']) > 0
    
    def test_retrieve_topics_with_similarity_scores(self, client):
        """Test that retrieved topics include similarity scores"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={
                'query': 'anxiety and stress management',
                'top_k': 3
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        topics = data['topics']
        for topic in topics:
            assert 'id' in topic
            assert 'title' in topic
            assert 'similarity_score' in topic
            assert 0 <= topic['similarity_score'] <= 1
    
    def test_retrieve_topics_missing_query(self, client):
        """Test missing query field"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'query' in data['error'].lower()
    
    def test_retrieve_topics_empty_query(self, client):
        """Test empty query string"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': '', 'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_retrieve_topics_invalid_top_k(self, client):
        """Test invalid top_k value"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'test', 'top_k': 100},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'top_k' in data['error'].lower()
    
    def test_retrieve_topics_custom_top_k(self, client):
        """Test with custom top_k values"""
        for top_k in [1, 5, 10, 15]:
            response = client.post(
                '/api/rag/retrieve-topics',
                json={'query': 'depression', 'top_k': top_k},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['topics_count'] <= top_k


class TestEndpointIntegration:
    """Integration tests for RAG endpoints"""
    
    def test_workflow_health_then_generate(self, client, sample_diary_entries):
        """Test workflow: check health, then generate suggestions"""
        # First check health
        health_response = client.get('/api/rag/health')
        assert health_response.status_code == 200
        
        # Then generate suggestions
        suggest_response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': sample_diary_entries,
                'top_k': 5
            },
            content_type='application/json'
        )
        
        assert suggest_response.status_code == 200
    
    def test_workflow_retrieve_then_analyze(self, client):
        """Test workflow: retrieve topics then analyze"""
        # Retrieve topics
        retrieve_response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'stress management', 'top_k': 3},
            content_type='application/json'
        )
        
        assert retrieve_response.status_code == 200
        retrieve_data = json.loads(retrieve_response.data)
        assert retrieve_data['topics_count'] > 0
    
    def test_all_endpoints_respond_with_timestamps(self, client, sample_diary_entries):
        """Test that all endpoints include timestamps in responses"""
        endpoints = [
            ('/api/rag/health', 'GET', None),
            ('/api/rag/index-stats', 'GET', None),
            ('/api/rag/generate-suggestions', 'POST', {'diary_entries': sample_diary_entries}),
            ('/api/rag/retrieve-topics', 'POST', {'query': 'test'})
        ]
        
        for endpoint, method, data in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data, content_type='application/json')
            
            if response.status_code in [200, 500]:  # Accept both success and error
                resp_data = json.loads(response.data)
                assert 'timestamp' in resp_data, f"Timestamp missing from {endpoint}"


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            '/api/rag/generate-suggestions',
            data='{invalid json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Test handling of missing content-type"""
        response = client.post(
            '/api/rag/generate-suggestions',
            data='test'
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [400, 415]
    
    def test_invalid_entry_format(self, client):
        """Test handling of invalid entry format"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': [
                    {
                        'date': '2026-01-16'
                        # Missing 'content' field
                    }
                ]
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'


if __name__ == '__main__': 
    pytest.main([__file__, '-v'])