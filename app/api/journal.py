"""
Journal API - Flask version
Handles diary entries
"""

from flask import Blueprint, request, jsonify
from app.database import get_db
import jwt
import os
from datetime import datetime
from functools import wraps

journal_bp = Blueprint('journal', __name__)

# Authentication decorator
def token_required(f):
    """Decorator to require JWT token for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # "Bearer <token>"
            except IndexError: 
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(
                token,
                os.environ.get('SECRET_KEY', 'morningtide-secret-key-2026'),
                algorithms=['HS256']
            )
            request. current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Handle OPTIONS preflight requests
@journal_bp.route('/entries', methods=['OPTIONS'])
def options_entries():
    """Handle CORS preflight for /entries"""
    return jsonify({}), 204

@journal_bp.route('/entries/<int:entry_id>', methods=['OPTIONS'])
def options_entry(entry_id):
    """Handle CORS preflight for /entries/<id>"""
    return jsonify({}), 204

@journal_bp.route('/entries', methods=['POST'])
@token_required
def create_entry():
    """
    Create a new journal entry
    
    Request body:
        {
            "content": "string",
            "date": "YYYY-MM-DD"
        }
    
    Returns:
        {
            "message": "Entry created successfully",
            "id": int,
            "date": "YYYY-MM-DD"
        }
    """
    try:
        data = request.get_json()
        
        if not data:  
            return jsonify({'message':   'No data provided'}), 400
        
        content = data.get('content', '').strip()
        date = data.get('date')
        
        # Validation
        if not content:  
            return jsonify({'message':   'Content is required'}), 400
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get user from token
        user_id = request.current_user. get('user_id')
        
        # Check if entry already exists for this date
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT id FROM journal_entries WHERE user_id = ? AND date = ? ',
            (user_id, date)
        )
        existing_entry = cursor.fetchone()
        
        if existing_entry:
            # Update existing entry
            cursor.execute(
                'UPDATE journal_entries SET content = ?   WHERE id = ?',
                (content, existing_entry['id'])
            )
            db.commit()
            entry_id = existing_entry['id']
            message = 'Entry updated successfully'
        else:
            # Create new entry
            cursor.execute(
                'INSERT INTO journal_entries (user_id, content, date, created_at) VALUES (?, ?, ?, ?)',
                (user_id, content, date, datetime.utcnow())
            )
            db.commit()
            entry_id = cursor.lastrowid
            message = 'Entry created successfully'
        
        return jsonify({
            'message': message,
            'id': entry_id,
            'date': date
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating entry: {str(e)}")
        return jsonify({'message':   f'Failed to create entry: {str(e)}'}), 500

@journal_bp.route('/entries', methods=['GET'])
@token_required
def get_entries():
    """
    Get journal entries for a date range
    
    Query parameters: 
        start_date:   YYYY-MM-DD (optional)
        end_date: YYYY-MM-DD (optional)
    
    Returns:
        [
            {
                "id":   int,
                "content": "string",
                "date": "YYYY-MM-DD",
                "created_at": "timestamp",
                "analysis": {...  } or null
            }
        ]
    """
    try:
        user_id = request.current_user.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        db = get_db()
        cursor = db.cursor()
        
        # Build query based on parameters
        if start_date and end_date:
            query = '''
                SELECT e.*, a.emotion_score, a.top_emotions, a.analyzed_at
                FROM journal_entries e
                LEFT JOIN analysis_results a ON e. id = a.entry_id
                WHERE e.user_id = ? AND e.date BETWEEN ?  AND ?
                ORDER BY e. date DESC
            '''
            cursor.execute(query, (user_id, start_date, end_date))
        else:
            query = '''
                SELECT e. *, a.emotion_score, a.top_emotions, a.analyzed_at
                FROM journal_entries e
                LEFT JOIN analysis_results a ON e.id = a. entry_id
                WHERE e. user_id = ? 
                ORDER BY e.date DESC
            '''
            cursor.execute(query, (user_id,))
        
        entries = cursor.fetchall()
        
        # Format results
        result = []
        for entry in entries:
            entry_dict = {
                'id': entry['id'],
                'content':   entry['content'],
                'date': entry['date'],
                'created_at': entry['created_at'],
                'analysis':  None
            }
            
            # Add analysis if exists
            if entry['emotion_score']: 
                import json
                entry_dict['analysis'] = {
                    'emotion_score':  entry['emotion_score'],
                    'top_emotions': json.loads(entry['top_emotions']),
                    'analyzed_at': entry['analyzed_at']
                }
            
            result. append(entry_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error getting entries:  {str(e)}")
        return jsonify({'message':  f'Failed to get entries: {str(e)}'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['GET'])
@token_required
def get_entry(entry_id):
    """Get a specific journal entry"""
    try:
        user_id = request.current_user.get('user_id')
        
        db = get_db()
        cursor = db. cursor()
        cursor.execute(
            '''
            SELECT e.*, a.emotion_score, a.top_emotions, a.analyzed_at
            FROM journal_entries e
            LEFT JOIN analysis_results a ON e.id = a.entry_id
            WHERE e.id = ?  AND e.user_id = ?  
            ''',
            (entry_id, user_id)
        )
        entry = cursor.fetchone()
        
        if not entry: 
            return jsonify({'message':  'Entry not found'}), 404
        
        result = {
            'id': entry['id'],
            'content':   entry['content'],
            'date': entry['date'],
            'created_at': entry['created_at'],
            'analysis':  None
        }
        
        if entry['emotion_score']:
            import json
            result['analysis'] = {
                'emotion_score': entry['emotion_score'],
                'top_emotions': json. loads(entry['top_emotions']),
                'analyzed_at':   entry['analyzed_at']
            }
        
        return jsonify(result), 200
        
    except Exception as e:  
        print(f"❌ Error getting entry: {str(e)}")
        return jsonify({'message': f'Failed to get entry: {str(e)}'}), 500


@journal_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@token_required
def delete_entry(entry_id):
    """
    Delete a journal entry
    
    Returns:
        {
            "message": "Entry deleted successfully",
            "id": int
        }
    """
    try:
        user_id = request.current_user.get('user_id')
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if entry exists and belongs to user
        cursor.execute(
            'SELECT id FROM journal_entries WHERE id = ? AND user_id = ?',
            (entry_id, user_id)
        )
        entry = cursor.fetchone()
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        # Delete associated analysis results first (foreign key constraint)
        cursor.execute('DELETE FROM analysis_results WHERE entry_id = ?', (entry_id,))
        
        # Delete the entry
        cursor.execute('DELETE FROM journal_entries WHERE id = ?', (entry_id,))
        
        db.commit()
        
        return jsonify({
            'message': 'Entry deleted successfully',
            'id':   entry_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error deleting entry:   {str(e)}")
        db.rollback()
        return jsonify({'message': f'Failed to delete entry: {str(e)}'}), 500