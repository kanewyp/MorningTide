"""
Unit tests for RAG endpoints

Tests individual RAG API endpoints with mocked dependencies. 
"""

import pytest
import json
from datetime import datetime, timedelta


class TestGenerateSuggestions:
    """Test therapy suggestion generation endpoint"""
    
    def test_generate_suggestions_success(self, client, patch_rag_pipeline, sample_diary_entries):
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
        data = response.get_json()
        
        assert data['status'] == 'success'
        assert 'timestamp' in data
        assert 'diary_analysis' in data
        assert 'suggestions' in data
        assert 'model' in data
        assert data['model'] == 'mistral'
    
    def test_generate_suggestions_validates_entries(self, client, patch_rag_pipeline):
        """Test that endpoint validates diary entries format"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries':  [
                    {'date': '2026-01-16'}  # Missing 'content' field
                ]
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'content' in data['error'].  lower()
    
    def test_generate_suggestions_requires_entries(self, client, patch_rag_pipeline):
        """Test that diary_entries field is required"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'diary_entries' in data['error']. lower()
    
    def test_generate_suggestions_rejects_empty_entries(self, client, patch_rag_pipeline):
        """Test that empty entries list is rejected"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': []},
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_generate_suggestions_validates_top_k(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that top_k is validated"""
        invalid_values = [0, -5, 25, 100, 'invalid']
        
        for invalid_top_k in invalid_values: 
            response = client.post(
                '/api/rag/generate-suggestions',
                json={
                    'diary_entries': sample_diary_entries,
                    'top_k': invalid_top_k
                },
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
    
    def test_generate_suggestions_accepts_valid_top_k(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that valid top_k values are accepted"""
        for valid_top_k in [1, 5, 10, 15, 20]:
            response = client.post(
                '/api/rag/generate-suggestions',
                json={
                    'diary_entries': sample_diary_entries,
                    'top_k': valid_top_k
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
    
    def test_generate_suggestions_missing_rag_pipeline(self, client):
        """Test graceful handling when RAG pipeline not initialized"""
        # Don't patch - leave pipeline as None
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries':  [{'date': '2026-01-16', 'content': 'test'}]
            },
            content_type='application/json'
        )
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'not initialized' in data['error']. lower()
    
    def test_generate_suggestions_includes_timestamps(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that response includes timestamp"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': sample_diary_entries},
            content_type='application/json'
        )
        
        data = response.get_json()
        assert 'timestamp' in data
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(data['timestamp'])


class TestHealthCheck:
    """Test RAG health check endpoint"""
    
    def test_health_check_success(self, client, patch_rag_pipeline):
        """Test successful health check"""
        response = client.get('/api/rag/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'status' in data
        assert 'embedder' in data
        assert 'vector_store' in data
        assert 'generator' in data
        assert 'timestamp' in data
    
    def test_health_check_includes_embedder_info(self, client, patch_rag_pipeline):
        """Test health check includes embedder information"""
        response = client.get('/api/rag/health')
        data = response.get_json()
        
        embedder = data['embedder']
        assert embedder['model'] == 'all-MiniLM-L6-v2'
        assert embedder['dimension'] == 384
        assert embedder['device'] == 'cpu'
    
    def test_health_check_without_rag_pipeline(self, client):
        """Test health check when RAG not initialized"""
        response = client. get('/api/rag/health')
        
        assert response. status_code == 503
        data = response.get_json()
        assert data['status'] == 'unhealthy'


class TestIndexStats:
    """Test vector store index statistics endpoint"""
    
    def test_index_stats_success(self, client, patch_rag_pipeline):
        """Test successful index stats retrieval"""
        response = client. get('/api/rag/index-stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_documents' in data
        assert isinstance(data['total_documents'], int)
        assert data['dimension'] == 384
        assert 'store_path' in data
        assert 'index_file_exists' in data
        assert 'metadata_file_exists' in data
    
    def test_index_stats_without_rag_pipeline(self, client):
        """Test index stats when RAG not initialized"""
        response = client.get('/api/rag/index-stats')
        
        assert response.status_code == 503


class TestRetrieveTopics:
    """Test topic retrieval endpoint"""
    
    def test_retrieve_topics_success(self, client, patch_rag_pipeline):
        """Test successful topic retrieval"""
        response = client. post(
            '/api/rag/retrieve-topics',
            json={
                'query': 'I am feeling anxious',
                'top_k': 5
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['status'] == 'success'
        assert 'query' in data
        assert 'topics_count' in data
        assert 'topics' in data
        assert isinstance(data['topics'], list)
    
    def test_retrieve_topics_requires_query(self, client, patch_rag_pipeline):
        """Test that query field is required"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'query' in data['error']. lower()
    
    def test_retrieve_topics_rejects_empty_query(self, client, patch_rag_pipeline):
        """Test that empty query is rejected"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': '', 'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
    
    def test_retrieve_topics_validates_top_k(self, client, patch_rag_pipeline):
        """Test top_k validation for retrieve topics"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'anxiety', 'top_k': 100},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'top_k' in data['error']. lower()
    
    def test_retrieve_topics_with_similarity_scores(self, client, patch_rag_pipeline):
        """Test that retrieved topics include similarity scores"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'stress management', 'top_k': 3},
            content_type='application/json'
        )
        
        data = response.get_json()
        topics = data['topics']
        
        for topic in topics:
            assert 'similarity_score' in topic
            assert 0 <= topic['similarity_score'] <= 1


class TestRebuildIndex:
    """Test index rebuild endpoint"""
    
    def test_rebuild_index_success(self, client, patch_rag_pipeline, mocker):
        """Test successful index rebuild"""
        # Mock the indexer
        mock_indexer = mocker.MagicMock()
        mocker.patch(
            'app.api.  rag.  TherapyCorpusIndexer',
            return_value=mock_indexer
        )
        
        response = client.post('/api/rag/rebuild-index')
        
        assert response. status_code == 200
        data = response.get_json()
        assert 'rebuild' in data['status']. lower()
    
    def test_rebuild_index_without_rag_pipeline(self, client):
        """Test rebuild index when RAG not initialized"""
        response = client.post('/api/rag/rebuild-index')
        
        assert response.status_code == 503


class TestErrorHandling:
    """Test error handling in RAG endpoints"""
    
    def test_malformed_json_generates_400(self, client):
        """Test that malformed JSON returns 400"""
        response = client.post(
            '/api/rag/generate-suggestions',
            data='{invalid json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type_returns_400(self, client):
        """Test handling of missing content-type"""
        response = client.post(
            '/api/rag/generate-suggestions',
            data='test'
        )
        
        assert response.status_code in [400, 415]
    
    def test_all_rag_endpoints_return_timestamps(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that all endpoints return timestamps"""
        endpoints = [
            ('GET', '/api/rag/health', None),
            ('GET', '/api/rag/index-stats', None),
            ('POST', '/api/rag/generate-suggestions', {
                'diary_entries': sample_diary_entries
            }),
            ('POST', '/api/rag/retrieve-topics', {'query': 'test'})
        ]
        
        for method, endpoint, data in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(
                    endpoint,
                    json=data,
                    content_type='application/json'
                )
            
            if response.status_code in [200, 500]:
                resp_data = response.get_json()
                assert 'timestamp' in resp_data


class TestDataValidation:
    """Test request data validation"""
    
    @pytest.mark.parametrize('invalid_date,invalid_content', [
        ('invalid-date', 'content'),
        ('2026-01-16', 123),  # content must be string
        (None, 'content'),
        ('2026-01-16', None),
    ])
    def test_diary_entry_type_validation(
        self,
        client,
        patch_rag_pipeline,
        invalid_date,
        invalid_content
    ):
        """Test type validation for diary entries"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': [
                    {'date': invalid_date, 'content': invalid_content}
                ]
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_very_long_diary_entry(self, client, patch_rag_pipeline):
        """Test handling of very long diary entries"""
        long_content = "x" * 100000  # 100k characters
        
        response = client.post(
            '/api/rag/generate-suggestions',
            json={
                'diary_entries': [
                    {
                        'date': '2026-01-16',
                        'content': long_content
                    }
                ]
            },
            content_type='application/json'
        )
        
        # Should either succeed or handle gracefully
        assert response.status_code in [200, 400, 413]
    
    def test_special_characters_in_query(self, client, patch_rag_pipeline):
        """Test handling of special characters in query"""
        special_queries = [
            "I'm feeling 😊 happy! ",
            "Query with <tags>",
            'Query with "quotes"',
            "Query with 'apostrophes'",
            "Query with \\backslashes\\",
        ]
        
        for query in special_queries: 
            response = client.post(
                '/api/rag/retrieve-topics',
                json={'query': query, 'top_k': 3},
                content_type='application/json'
            )
            
            # Should handle special characters gracefully
            assert response. status_code in [200, 400]