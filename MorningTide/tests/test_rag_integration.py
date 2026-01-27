"""
Integration tests for RAG system

Tests interaction between different components of the RAG system. 
"""

import pytest
import json
from datetime import datetime


class TestRAGWorkflow:
    """Test complete RAG workflows"""
    
    def test_full_suggestion_generation_workflow(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test complete workflow:  health check -> generate suggestions"""
        # First, verify system is healthy
        health_response = client.get('/api/rag/health')
        assert health_response.status_code == 200
        
        health_data = health_response.get_json()
        assert health_data['status'] == 'healthy'
        
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
        suggest_data = suggest_response.get_json()
        assert suggest_data['status'] == 'success'
        assert suggest_data['diary_analysis']['entry_count'] == 3
    
    def test_retrieve_then_analyze_workflow(self, client, patch_rag_pipeline):
        """Test workflow: retrieve topics -> analyze retrieved topics"""
        # Retrieve topics
        retrieve_response = client. post(
            '/api/rag/retrieve-topics',
            json={'query': 'managing anxiety and stress', 'top_k': 5},
            content_type='application/json'
        )
        
        assert retrieve_response.status_code == 200
        retrieve_data = retrieve_response.get_json()
        assert retrieve_data['topics_count'] > 0
        
        # Verify topics have required fields
        for topic in retrieve_data['topics']:
            assert 'id' in topic
            assert 'title' in topic
            assert 'category' in topic
            assert 'similarity_score' in topic
    
    def test_multiple_consecutive_requests(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test multiple consecutive API calls don't interfere"""
        queries = [
            {'diary_entries': sample_diary_entries, 'top_k': 3},
            {'diary_entries':  sample_diary_entries, 'top_k': 5},
            {'diary_entries':  sample_diary_entries[: 1], 'top_k':  4},
        ]
        
        for query in queries:
            response = client.post(
                '/api/rag/generate-suggestions',
                json=query,
                content_type='application/json'
            )
            assert response.status_code == 200
    
    def test_concurrent_topic_retrieval(self, client, patch_rag_pipeline):
        """Test multiple concurrent topic retrieval requests"""
        queries = [
            'anxiety management',
            'depression support',
            'stress relief',
            'sleep issues',
            'relationship problems'
        ]
        
        for query in queries:
            response = client.post(
                '/api/rag/retrieve-topics',
                json={'query': query, 'top_k': 3},
                content_type='application/json'
            )
            assert response.status_code == 200


class TestResponseConsistency:
    """Test consistency of API responses"""
    
    def test_suggest_response_structure(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that suggestion response has expected structure"""
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': sample_diary_entries},
            content_type='application/json'
        )
        
        data = response.get_json()
        
        # Required fields
        required_fields = [
            'status', 'timestamp', 'diary_analysis',
            'retrieved_topics_count', 'suggestions', 'model'
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Nested required fields in diary_analysis
        analysis_fields = ['entry_count', 'date_range', 'themes']
        for field in analysis_fields:
            assert field in data['diary_analysis']
    
    def test_retrieve_response_structure(self, client, patch_rag_pipeline):
        """Test that retrieve response has expected structure"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'test', 'top_k': 3},
            content_type='application/json'
        )
        
        data = response.get_json()
        
        required_fields = ['status', 'query', 'topics_count', 'topics', 'timestamp']
        for field in required_fields:
            assert field in data
    
    def test_health_check_consistency(self, client, patch_rag_pipeline):
        """Test that health check returns consistent structure"""
        for _ in range(3):
            response = client.get('/api/rag/health')
            data = response.get_json()
            
            required_sections = ['embedder', 'vector_store', 'generator']
            for section in required_sections:
                assert section in data


class TestErrorRecovery:
    """Test error handling and recovery"""
    
    def test_invalid_request_doesnt_break_next_request(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test that invalid request doesn't affect next valid request"""
        # Send invalid request
        invalid_response = client.post(
            '/api/rag/generate-suggestions',
            json={'invalid': 'data'},
            content_type='application/json'
        )
        assert invalid_response.status_code == 400
        
        # Next valid request should work
        valid_response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': sample_diary_entries},
            content_type='application/json'
        )
        assert valid_response.status_code == 200
    
    def test_malformed_json_recovery(self, client, patch_rag_pipeline):
        """Test recovery from malformed JSON"""
        # Send malformed
        bad_response = client.post(
            '/api/rag/retrieve-topics',
            data='invalid',
            content_type='application/json'
        )
        assert bad_response.status_code == 400
        
        # Next request should work
        good_response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'test'},
            content_type='application/json'
        )
        assert good_response.status_code == 200


class TestEndpointInteraction:
    """Test interactions between different endpoints"""
    
    def test_health_then_suggest_workflow(self, client, patch_rag_pipeline, sample_diary_entries):
        """Test health check before suggestion generation"""
        # Check health
        health = client.get('/api/rag/health')
        assert health. status_code == 200
        
        # Generate suggestions
        suggest = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': sample_diary_entries},
            content_type='application/json'
        )
        assert suggest.status_code == 200
    
    def test_stats_consistency_across_calls(self, client, patch_rag_pipeline):
        """Test that index stats remain consistent"""
        stats1 = client.get('/api/rag/index-stats').get_json()
        
        # Make some requests
        for _ in range(3):
            client.post(
                '/api/rag/retrieve-topics',
                json={'query': 'test'},
                content_type='application/json'
            )
        
        stats2 = client.get('/api/rag/index-stats').get_json()
        
        # Stats should be same
        assert stats1['total_documents'] == stats2['total_documents']
        assert stats1['dimension'] == stats2['dimension']


class TestDataThroughput:
    """Test API with various data volumes"""
    
    def test_many_diary_entries(self, client, patch_rag_pipeline):
        """Test handling of many diary entries"""
        entries = [
            {
                'date': f'2025-12-{i:02d}',
                'content': f'Entry {i}:  Reflecting on day {i}.  ' * 10
            }
            for i in range(1, 8)
        ]
        
        response = client.post(
            '/api/rag/generate-suggestions',
            json={'diary_entries': entries, 'top_k': 5},
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_high_top_k_retrieval(self, client, patch_rag_pipeline):
        """Test retrieval with high top_k value"""
        response = client.post(
            '/api/rag/retrieve-topics',
            json={'query': 'mental health', 'top_k':  20},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['topics_count'] <= 20