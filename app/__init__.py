"""
Application Factory - MorningTide Flask Application

Initializes Flask app with all blueprints, database, ML models, and RAG pipeline. 
"""

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG pipeline instance
_rag_pipeline = None


def get_rag_pipeline():
    """Get the global RAG pipeline instance"""
    global _rag_pipeline
    return _rag_pipeline


def set_rag_pipeline(pipeline):
    """Set the global RAG pipeline instance"""
    global _rag_pipeline
    _rag_pipeline = pipeline


def initialize_rag_pipeline():
    """Initialize the RAG pipeline with configuration"""
    global _rag_pipeline
    
    try:
        from app.config import Config
        from app.ml. rag. runner import RAGPipeline
        from app.ml. rag.indexer import TherapyCorpusIndexer
        
        logger.info("🧠 Initializing RAG pipeline...")
        
        # Create RAG pipeline instance
        _rag_pipeline = RAGPipeline(
            embedding_model=Config.EMBEDDING_MODEL,
            embedding_device=Config.EMBEDDING_DEVICE,
            vector_store_path=Config.VECTOR_STORE_PATH,
            ollama_base_url=Config.OLLAMA_BASE_URL,
            ollama_model=Config.OLLAMA_MODEL,
            chunk_size=Config.RAG_CHUNK_SIZE,
            chunk_overlap=Config.RAG_CHUNK_OVERLAP,
            top_k_retrieval=Config.RAG_TOP_K_RETRIEVAL,
            max_context_tokens=Config.RAG_CONTEXT_WINDOW
        )
        
        # Initialize corpus index if empty
        if _rag_pipeline.vector_store.index. ntotal == 0:
            logger.info("📚 Vector store is empty, building index from corpus...")
            indexer = TherapyCorpusIndexer(
                _rag_pipeline.embedder,
                _rag_pipeline.vector_store
            )
            indexer.build_index(Config.RAG_CORPUS_PATH)
            logger.info("✓ Corpus index built successfully")
        else:
            logger.info(
                f"✓ Using existing index with "
                f"{_rag_pipeline.vector_store.index.ntotal} documents"
            )
        
        logger.info("✅ RAG pipeline initialized successfully")
        return _rag_pipeline
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {e}", exc_info=True)
        logger.warning("⚠️  RAG functionality will not be available")
        return None


def create_app():
    """Create and configure Flask application"""
    
    print("🔄 Starting create_app()...")
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'morningtide-secret-key-2026'
    
    print("  → Configuring CORS...")
    # Enable CORS
    CORS(app, resources={
        r"/*": {
            "origins":  ["http://localhost:3000", "http://localhost:3001"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    print("  ✓ CORS configured")
    
    print("  → Initializing database...")
    # Initialize database
    from app.database import init_db, engine, Base
    Base.metadata.create_all(bind=engine)
    init_db()
    print("  ✓ Database initialized")
    
    print("  → Registering blueprints...")
    # Register auth routes (NO url_prefix - auth routes are at /auth directly)
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp)
    print("    ✓ Auth routes registered at /auth")
    
    # Register journal routes
    from app.api.journal import journal_bp
    app.register_blueprint(journal_bp, url_prefix='/api/journal')
    print("    ✓ Journal routes registered at /api/journal")
    
    # Register analysis routes
    from app.api.analysis import analysis_bp
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    print("    ✓ Analysis routes registered at /api/analysis")
    
    # Register RAG routes (NEW)
    try:
        from app.api.rag import rag_bp
        app.register_blueprint(rag_bp, url_prefix='/api/rag')
        print("    ✓ RAG routes registered at /api/rag")
    except ImportError as e:
        logger.warning(f"⚠️  Could not import RAG blueprint: {e}")
        print("    ⚠️  RAG routes not available")
    
    # Root route
    @app.route('/')
    def home():
        return {
            'message': 'MorningTide API',
            'status': 'running',
            'endpoints': {
                'auth': '/auth/signup, /auth/login, /auth/verify',
                'journal':  '/api/journal/entries',
                'analysis': '/api/analysis/analyze',
                'rag': '/api/rag/generate-suggestions, /api/rag/health'
            },
            'rag_enabled': get_rag_pipeline() is not None
        }

    @app.route('/health')
    def health():
        rag_status = "initialized" if get_rag_pipeline() else "not initialized"
        return {
            'status': 'healthy',
            'database': 'connected',
            'rag_pipeline': rag_status
        }

    # Handle CORS preflight for all routes
    @app. before_request
    def handle_preflight():
        if request. method == 'OPTIONS': 
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Origin', request. headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            response. headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 204

    # Load ML models and RAG pipeline on first request (NEW - ENHANCED)
    @app.before_request
    def load_ml_models():
        if not hasattr(load_ml_models, 'loaded'):
            try:
                # Load emotion classification model
                from app.ml. inference import emotion_classifier
                logger.info("✓ Emotion classification model loaded")
                print("✓ ML model loaded")
                
                # Initialize RAG pipeline
                logger.info("Initializing RAG pipeline...")
                initialize_rag_pipeline()
                
                load_ml_models.loaded = True
                
            except Exception as e:
                logger.warning(f"⚠️  ML model/RAG initialization warning: {e}")
                print(f"⚠️  ML/RAG initialization warning: {e}")
                load_ml_models.loaded = True

    # Global error handler for RAG-specific errors
    @app.errorhandler(RuntimeError)
    def handle_runtime_error(error):
        """Handle runtime errors (e.g., RAG pipeline not initialized)"""
        logger.error(f"Runtime error: {error}", exc_info=True)
        return {
            'status': 'error',
            'message': str(error)
        }, 500

    # Global error handler for general exceptions
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions"""
        logger. error(f"Unhandled exception: {error}", exc_info=True)
        return {
            'status': 'error',
            'message': 'Internal server error'
        }, 500

    print("✅ create_app() completed successfully\n")
    return app