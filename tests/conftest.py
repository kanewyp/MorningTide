"""
Pytest configuration and shared fixtures for all tests

Provides reusable fixtures for app, client, database, and sample data. 
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
import json

# Set testing environment
os.environ['TESTING'] = 'True'


@pytest.fixture(scope='session')
def test_config():
    """Test configuration fixture"""
    return {
        'TESTING': True,
        'DEBUG': False,
        'SQLALCHEMY_ECHO': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
    }


@pytest.fixture
def app(test_config):
    """Create application for testing"""
    from app import create_app
    from app.config import Config
    
    # Override config with test settings
    app = create_app()
    app.config.update(test_config)
    
    # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Create test database
    with app. app_context():
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        yield app
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app. test_client()


@pytest.fixture
def app_context(app):
    """Push app context for tests that need it"""
    with app. app_context():
        yield app


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_user_data():
    """Sample user registration data"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'age': 25,
        'gender': 'Other'
    }


@pytest.fixture
def sample_diary_entries():
    """Sample diary entries for testing"""
    today = datetime.now()
    return [
        {
            "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "content": "Today I felt anxious about my upcoming presentation. "
                      "I couldn't sleep well because of the anxiety and worry."
        },
        {
            "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "content": "Had the presentation today. It went better than expected, "
                      "but I'm still replaying it in my head.  Feeling a bit stressed."
        },
        {
            "date": today.strftime("%Y-%m-%d"),
            "content": "Trying to relax but my mind keeps racing. "
                      "I feel overwhelmed with everything on my plate.  Need to practice self-care."
        }
    ]


@pytest.fixture
def sample_journal_entry():
    """Single sample journal entry"""
    return {
        'title': 'Day in the Office',
        'content': 'Had a productive day at work. Completed the project milestone.',
        'mood': 'happy',
        'intensity': 7
    }


@pytest.fixture
def sample_text_for_analysis():
    """Sample text for analysis/emotion detection"""
    return {
        'text': 'I am so happy and excited about this wonderful opportunity! '
               'I cannot wait to start!'
    }


# ==================== Authentication Fixtures ====================

@pytest. fixture
def authenticated_user(client, sample_user_data, app_context):
    """Create and authenticate a test user"""
    from app.models. user import User
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Create user
        user = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            age=sample_user_data. get('age'),
            gender=sample_user_data.get('gender')
        )
        user.set_password(sample_user_data['password'])
        db.add(user)
        db.commit()
        
        # Return user data for auth
        return {
            'user': user,
            'credentials': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture
def auth_headers(client, authenticated_user):
    """Get authorization headers for authenticated requests"""
    credentials = authenticated_user['credentials']
    
    # Login to get token
    response = client.post(
        '/auth/login',
        json=credentials,
        content_type='application/json'
    )
    
    if response.status_code == 200:
        data = response.get_json()
        token = data. get('access_token')
        return {'Authorization': f'Bearer {token}'}
    
    return {}


# ==================== Mock/Patch Fixtures ====================

@pytest. fixture
def mock_ollama_response(mocker):
    """Mock Ollama LLM response"""
    def _mock_response(suggestions_text=None):
        default_suggestions = """DISCUSSION TOPIC 1: Managing Anxiety
- Context: Your entries show anxiety about presentations and overwhelm
- Therapy Connection: Cognitive Behavioral Therapy (CBT)
- Discussion Prompt: What specific thoughts trigger your anxiety?
- Suggested Focus: Develop coping strategies for presentation anxiety

DISCUSSION TOPIC 2: Stress Management
- Context:  You mentioned feeling overwhelmed
- Therapy Connection: Stress Management Techniques
- Discussion Prompt:  What activities help you relax?
- Suggested Focus:  Build a personal stress management plan"""
        
        return suggestions_text or default_suggestions
    
    return _mock_response


@pytest. fixture
def mock_rag_pipeline(mocker):
    """Mock RAG pipeline for testing without actual LLM"""
    mock_pipeline = mocker.MagicMock()
    mock_pipeline.generate_suggestions.return_value = {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'diary_analysis': {
            'entry_count': 3,
            'date_range': '2026-01-14 to 2026-01-16',
            'themes': ['anxiety', 'stress', 'overwhelm']
        },
        'retrieved_topics_count': 5,
        'suggestions': 'Mock therapy suggestions.. .',
        'model':  'mistral'
    }
    
    mock_pipeline.health_check.return_value = {
        'status': 'healthy',
        'embedder':  {
            'model': 'all-MiniLM-L6-v2',
            'dimension': 384,
            'device': 'cpu'
        },
        'vector_store': {
            'total_documents': 75,
            'dimension': 384
        },
        'generator': {
            'status': 'healthy',
            'model_available': True
        },
        'timestamp': datetime.now().isoformat()
    }
    
    mock_pipeline.retriever.retrieve.return_value = [
        {
            'id': 'anxiety_001',
            'category': 'Anxiety Management',
            'title': 'Understanding Anxiety Triggers',
            'content': 'Anxiety often stems from.. .',
            'keywords': ['anxiety', 'triggers'],
            'difficulty': 'beginner',
            'similarity_score': 0.92
        }
    ]
    
    return mock_pipeline


@pytest.fixture
def patch_rag_pipeline(mocker, mock_rag_pipeline):
    """Patch the global RAG pipeline in the app"""
    mocker.patch('app.get_rag_pipeline', return_value=mock_rag_pipeline)
    return mock_rag_pipeline