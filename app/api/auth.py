"""
Authentication API
Handles user signup and login
"""

from flask import Blueprint, request, jsonify
from app.database import get_db
import jwt
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Create a new user account
    
    Request body:
        {
            "username": "string",
            "password": "string"
        }
    
    Returns:
        {
            "message": "User created successfully",
            "token": "JWT token",
            "username":  "string"
        }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data: 
            return jsonify({'message':  'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username: 
            return jsonify({'message':  'Username is required'}), 400
        
        if not password:
            return jsonify({'message': 'Password is required'}), 400
        
        if len(username) < 3:
            return jsonify({'message': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({'message': 'Username already exists'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Create user
        cursor.execute(
            'INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
            (username, hashed_password, datetime.datetime.utcnow())
        )
        db.commit()
        user_id = cursor.lastrowid
        
        print(f"✅ New user created: {username} (ID: {user_id})")
        
        # Generate JWT token
        token = jwt.encode({
            'user_id':  user_id,
            'username': username,
            'exp':  datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, os.environ. get('SECRET_KEY', 'morningtide-secret-key-2026'), algorithm='HS256')
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'username': username
        }), 201
        
    except Exception as e:
        print(f"❌ Signup error: {str(e)}")
        return jsonify({'message': f'Signup failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login to existing account
    
    Request body: 
        {
            "username":  "string",
            "password":  "string"
        }
    
    Returns:
        {
            "message": "Login successful",
            "token": "JWT token",
            "username": "string"
        }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not password:
            return jsonify({'message': 'Username and password required'}), 400
        
        # Find user
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'Invalid username or password'}), 401
        
        # Verify password
        if not check_password_hash(user['password'], password):
            return jsonify({'message': 'Invalid username or password'}), 401
        
        print(f"✅ User logged in: {username}")
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, os.environ.get('SECRET_KEY', 'morningtide-secret-key-2026'), algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token':  token,
            'username': username
        }), 200
        
    except Exception as e: 
        print(f"❌ Login error: {str(e)}")
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify JWT token is valid"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header: 
            return jsonify({'message': 'No token provided'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        payload = jwt.decode(
            token,
            os.environ.get('SECRET_KEY', 'morningtide-secret-key-2026'),
            algorithms=['HS256']
        )
        
        return jsonify({
            'valid': True,
            'username': payload['username']
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401