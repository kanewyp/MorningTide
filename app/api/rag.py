"""
RAG API Endpoints - Flask Blueprint

Provides endpoints for generating therapy suggestions, health checks,
and index management using local RAG pipeline.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import get_rag_pipeline


logger = logging.getLogger(__name__)

# Create Blueprint
rag_bp = Blueprint('rag', __name__)


# ==================== Request Validation Helpers ====================

def validate_diary_entries(data):
    """Validate diary entries format"""
    if not isinstance(data, dict):
        return False, "Request body must be JSON object"
    
    if 'diary_entries' not in data: 
        return False, "Missing 'diary_entries' field"
    
    entries = data. get('diary_entries', [])
    if not isinstance(entries, list) or len(entries) == 0:
        return False, "diary_entries must be a non-empty list"
    
    # Validate each entry
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return False, f"Entry {i} must be a JSON object"
        
        if 'date' not in entry or 'content' not in entry: 
            return False, f"Entry {i} missing 'date' or 'content' field"
        
        if not isinstance(entry['date'], str) or not isinstance(entry['content'], str):
            return False, f"Entry {i}:  'date' and 'content' must be strings"
    
    return True, None


# ==================== Endpoints ====================

@rag_bp.route('/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """
    Generate personalized therapy suggestions based on diary entries. 
    
    Request JSON: 
    {
        "diary_entries": [
            {
                "date": "2026-01-16",
                "content": "Today I felt overwhelmed..."
            }
        ],
        "top_k": 5,
        "stream":  false
    }
    
    Returns:
    {
        "status": "success",
        "timestamp": "2026-01-16T14:30:00",
        "diary_analysis": {
            "entry_count": 1,
            "date_range": "2026-01-16",
            "themes": ["anxiety", "work"]
        },
        "retrieved_topics_count": 5,
        "suggestions": "DISCUSSION TOPIC 1: .. .",
        "model":  "mistral"
    }
    """
    try:
        # Get RAG pipeline
        pipeline = get_rag_pipeline()
        if not pipeline:
            return jsonify({
                "status": "error",
                "error": "RAG pipeline not initialized",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # Validate request
        data = request.get_json()
        if data is None:
            return jsonify({
                "status": "error",
                "error": "Request body must be JSON",
                "timestamp":  datetime.now().isoformat()
            }), 400
        
        is_valid, error_msg = validate_diary_entries(data)
        if not is_valid:
            return jsonify({
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Extract parameters
        diary_entries = data.get('diary_entries', [])
        top_k = data.get('top_k', 5)
        stream = data.get('stream', False)
        
        # Validate parameters
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            return jsonify({
                "status": "error",
                "error": "top_k must be integer between 1 and 20",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        logger.info(f"Generating suggestions for {len(diary_entries)} entries")
        
        # Update retrieval count
        original_top_k = pipeline.top_k_retrieval
        pipeline.top_k_retrieval = top_k
        
        try:
            # Generate suggestions
            result = pipeline.generate_suggestions(
                diary_entries=diary_entries,
                stream=stream
            )
        finally:
            # Restore original top_k
            pipeline.top_k_retrieval = original_top_k
        
        # Check for errors
        if result. get("status") == "error":
            return jsonify({
                "status": "error",
                "error": result.get('error'),
                "timestamp": result.get('timestamp')
            }), 500
        
        # Build response
        response = {
            "status": result.get("status", "success"),
            "timestamp":  result.get("timestamp"),
            "diary_analysis": result.get("diary_analysis", {}),
            "retrieved_topics_count":  result.get("retrieved_topics_count", 0),
            "suggestions": result.get("suggestions", ""),
            "model": result.get("model", "")
        }
        
        return jsonify(response), 200
        
    except Exception as e: 
        logger.error(f"Error generating suggestions: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}",
            "timestamp":  datetime.now().isoformat()
        }), 500


@rag_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check health of RAG system components.
    
    Returns status of:
    - Embedding model
    - Vector store
    - LLM connection
    """
    try:
        pipeline = get_rag_pipeline()
        
        if not pipeline:
            return jsonify({
                "status": "unhealthy",
                "error":  "RAG pipeline not initialized",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        health = pipeline.health_check()
        
        return jsonify({
            "status":  health.get("status", "unknown"),
            "embedder": health.get("embedder", {}),
            "vector_store":  health.get("vector_store", {}),
            "generator": health.get("generator", {}),
            "timestamp": health.get("timestamp")
        }), 200
        
    except Exception as e: 
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@rag_bp.route('/rebuild-index', methods=['POST'])
def rebuild_index():
    """
    Rebuild the FAISS vector index from the therapy corpus.
    
    This endpoint reloads and re-indexes the therapy corpus. 
    Returns immediately; rebuild runs in background.
    
    Returns:
    {
        "status": "rebuild_complete",
        "message": "Index rebuild successful",
        "timestamp": "2026-01-16T14:30:00"
    }
    """
    try:
        pipeline = get_rag_pipeline()
        if not pipeline: 
            return jsonify({
                "status": "error",
                "error": "RAG pipeline not initialized",
                "timestamp": datetime. now().isoformat()
            }), 503
        
        logger.info("Starting index rebuild...")
        
        try:
            from app.ml. rag. indexer import TherapyCorpusIndexer
            from app.config import Config
            
            indexer = TherapyCorpusIndexer(
                pipeline. embedder,
                pipeline.vector_store
            )
            
            indexer.build_index(Config.RAG_CORPUS_PATH)
            
            logger.info("✓ Index rebuild complete")
            
            return jsonify({
                "status": "rebuild_complete",
                "message": "Index rebuild successful",
                "timestamp": datetime. now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}", exc_info=True)
            return jsonify({
                "status": "error",
                "error": f"Index rebuild failed: {str(e)}",
                "timestamp": datetime. now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"Rebuild index error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime. now().isoformat()
        }), 500


@rag_bp.route('/index-stats', methods=['GET'])
def get_index_stats():
    """
    Get current vector store index statistics.
    
    Returns:
    {
        "total_documents": 75,
        "dimension": 384,
        "store_path": "./data/vector_store",
        "index_file_exists": true,
        "metadata_file_exists": true
    }
    """
    try:
        pipeline = get_rag_pipeline()
        if not pipeline:
            return jsonify({
                "status": "error",
                "error": "RAG pipeline not initialized",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        stats = pipeline.vector_store.get_stats()
        
        return jsonify({
            "total_documents": stats.get("total_documents", 0),
            "dimension": stats.get("dimension", 0),
            "store_path": stats.get("store_path", ""),
            "index_file_exists": stats.get("index_file_exists", False),
            "metadata_file_exists": stats.get("metadata_file_exists", False)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Failed to get stats: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@rag_bp.route('/retrieve-topics', methods=['POST'])
def retrieve_topics():
    """
    Retrieve relevant therapy topics for a query.
    
    Request JSON: 
    {
        "query":  "I'm feeling anxious about work",
        "top_k":  5
    }
    
    Returns:
    {
        "status": "success",
        "query": "I'm feeling anxious about work",
        "topics_count": 5,
        "topics": [...]
    }
    """
    try:
        pipeline = get_rag_pipeline()
        if not pipeline:
            return jsonify({
                "status": "error",
                "error": "RAG pipeline not initialized",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # Validate request
        data = request. get_json()
        if data is None:
            return jsonify({
                "status": "error",
                "error": "Request body must be JSON",
                "timestamp":  datetime.now().isoformat()
            }), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                "status": "error",
                "error": "Query field is required and cannot be empty",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        top_k = data.get('top_k', 5)
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            return jsonify({
                "status": "error",
                "error": "top_k must be integer between 1 and 20",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        logger.info(f"Retrieving topics for query: {query[:50]}...")
        
        # Retrieve topics
        topics = pipeline.retriever.retrieve(query, k=top_k)
        
        return jsonify({
            "status":  "success",
            "query":  query,
            "topics_count": len(topics),
            "topics": topics,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger. error(f"Failed to retrieve topics: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Failed to retrieve topics: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# Add this at the end of app/api/rag.py, after all the route definitions

@rag_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        "status": "error",
        "error": "Bad request",
        "timestamp": datetime.now().isoformat()
    }), 400


@rag_bp.errorhandler(415)
def unsupported_media_type(error):
    """Handle unsupported media type errors"""
    return jsonify({
        "status": "error",
        "error": "Unsupported media type",
        "timestamp": datetime.now().isoformat()
    }), 415