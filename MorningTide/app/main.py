from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    This is a legacy entry point.
    The main create_app() is now in app/__init__.py
    This exists for backwards compatibility.
    """
    from app import create_app as main_create_app
    return main_create_app()


if __name__ == "__main__": 
    print("\n" + "="*60)
    print("🚀 MorningTide Flask Server Starting...")
    print("="*60 + "\n")
    
    app = create_app()
    
    if app is None:  
        print("\n❌ FATAL: create_app() returned None - check errors above")
        exit(1)
    
    print("\n✓ Flask app ready")
    print("📍 Starting server on http://0.0.0.0:8000\n")
    
    try:
        app.run(host="0.0.0.0", port=8000, debug=True)
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)