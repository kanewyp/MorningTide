"""
MorningTide Backend Server
Entry point for running the Flask application
"""

import os
from app import create_app

# Create the Flask app instance
app = create_app()

if __name__ == '__main__': 
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    # Get debug mode from environment or default to True for development
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("🌊 MorningTide Backend Server Starting...")
    print("=" * 50)
    print(f"📍 Running on:  http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🗄️  Database: morningtide.db")
    print("=" * 50)
    print("\n✅ Server is ready!  Press CTRL+C to quit.\n")
    
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Accept connections from any IP
        port=port,
        debug=debug,
        use_reloader=debug  # Auto-reload on code changes
    )