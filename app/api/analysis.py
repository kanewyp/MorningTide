"""
Analysis API - Flask version (cleaned)
Handles emotion analysis of journal entries
"""

from flask import Blueprint, request, jsonify
from app.database import get_db
from app. config import Config
import jwt
import os
from datetime import datetime
from functools import wraps
import json

analysis_bp = Blueprint("analysis", __name__)

# Authentication decorator
def token_required(f):
    """Decorator to require JWT token for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header:    
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Invalid token format"}), 401

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            payload = jwt.decode(
                token,
                os.environ.get("SECRET_KEY", "morningtide-secret-key-2026"),
                algorithms=["HS256"],
            )
            # attach user info to request
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated

# Handle OPTIONS preflight requests
@analysis_bp.route("/analyze", methods=["OPTIONS"])
def options_analyze():
    """Handle CORS preflight for /analyze"""
    return jsonify({}), 204

@analysis_bp.route("/<int:entry_id>", methods=["OPTIONS"])
def options_analysis(entry_id):
    """Handle CORS preflight for /<id>"""
    return jsonify({}), 204

@analysis_bp.route("/analyze", methods=["POST"])
@token_required
def analyze_entry():
    """
    POST /api/analyze
    Body:    { "entry_id": int } OR { "text": "..." }
    """
    try:  
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        entry_id = data.get("entry_id")
        text = data.get("text")

        if not entry_id and not text:
            return jsonify({"message": "entry_id or text is required"}), 400

        user_id = request.current_user.get("user_id")

        # If entry_id provided, fetch the journal content
        if entry_id:  
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT * FROM journal_entries WHERE id = ?  AND user_id = ?",
                (entry_id, user_id),
            )
            entry = cursor.fetchone()
            if not entry:
                return jsonify({"message": "Entry not found"}), 404
            text = entry["content"]

        print(f"🔍 Analyzing text for user {user_id}...")
        print(f"📊 Using importance method: {Config.DEFAULT_IMPORTANCE_METHOD}")

        # Run ML inference (import inside to allow fallback if ML not available)
        try:
            from app.ml. inference import analyze_emotion

            # Pass the importance method from config
            result = analyze_emotion(
                text, 
                adaptive=True,
                importance_method=Config.DEFAULT_IMPORTANCE_METHOD  # ✅ USE ML METHOD FROM CONFIG
            )

            top_emotion = result. get("top_emotion", "neutral")
            emotional_intensity = result.get("emotional_intensity", 5.0)
            all_scores = result.get("all_scores", {})

            print(f"✅ Top emotion: {top_emotion}, Intensity: {emotional_intensity}")

            # Score on 1-10
            emotion_score = int(emotional_intensity)
            positive_emotions = ["joy", "love", "surprise", "admiration", "optimism", "gratitude"]
            negative_emotions = ["sadness", "anger", "fear", "disgust", "disappointment"]
            if top_emotion in positive_emotions:    
                emotion_score = min(10, emotion_score + 2)
            elif top_emotion in negative_emotions:
                emotion_score = max(1, emotion_score - 2)
            emotion_score = max(1, min(10, emotion_score))

            sorted_emotions = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[: 3]
            top_emotions = [{"emotion": e, "probability": float(p)} for e, p in sorted_emotions]

        except ImportError as e:
            print("⚠️ ML model not available:", e)
            # Mock fallback
            emotion_score = 7
            top_emotions = [
                {"emotion": "joy", "probability": 0.6},
                {"emotion": "optimism", "probability": 0.25},
                {"emotion": "contentment", "probability": 0.15},
            ]
        except Exception as e:
            print("⚠️ ML analysis failed:", e)
            emotion_score = 5
            top_emotions = [
                {"emotion": "neutral", "probability": 0.8},
                {"emotion": "calm", "probability": 0.15},
                {"emotion": "thoughtful", "probability": 0.05},
            ]

        # Persist analysis if tied to an entry_id
        if entry_id:   
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM analysis_results WHERE entry_id = ? ", (entry_id,))
            existing_analysis = cursor.fetchone()
            analyzed_at = datetime.utcnow().isoformat()

            if existing_analysis:
                cursor. execute(
                    "UPDATE analysis_results SET emotion_score = ?, top_emotions = ?, analyzed_at = ?  WHERE entry_id = ?",
                    (emotion_score, json.dumps(top_emotions), analyzed_at, entry_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO analysis_results (entry_id, emotion_score, top_emotions, analyzed_at) VALUES (?, ?, ?, ?)",
                    (entry_id, emotion_score, json.dumps(top_emotions), analyzed_at),
                )
            db.commit()
            print(f"✅ Analysis saved to database for entry {entry_id}")

        response = {
            "emotion_score": emotion_score,
            "top_emotions": top_emotions,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
        if entry_id:
            response["entry_id"] = entry_id

        return jsonify(response), 200

    except Exception as e:    
        print("❌ Error analyzing:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Failed to analyze: {str(e)}"}), 500


@analysis_bp.route("/<int:entry_id>", methods=["GET"])
@token_required
def get_analysis(entry_id):
    """
    GET /api/analysis/<entry_id>
    Returns saved analysis for a given entry (if any)
    """
    try:
        user_id = request.current_user.get("user_id")
        db = get_db()
        cursor = db.cursor()
        
        # SECURITY:  Verify entry belongs to user before returning analysis
        cursor.execute(
            "SELECT id FROM journal_entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id)
        )
        entry_check = cursor.fetchone()
        if not entry_check:
            return jsonify({"message": "Entry not found or unauthorized"}), 404
        
        # Fetch analysis results
        cursor.execute(
            "SELECT emotion_score, top_emotions, analyzed_at FROM analysis_results WHERE entry_id = ?",
            (entry_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"message": "Analysis not found"}), 404

        # sqlite3.Row works like a dict, so use dict-style access directly
        emotion_score = row["emotion_score"]
        top_emotions_raw = row["top_emotions"]
        analyzed_at = row["analyzed_at"]

        # Parse JSON if it's a string
        top_emotions = json.loads(top_emotions_raw) if isinstance(top_emotions_raw, str) else top_emotions_raw

        print(f"✅ Analysis retrieved for entry {entry_id}")

        return jsonify(
            {
                "entry_id": entry_id,
                "emotion_score": emotion_score,
                "top_emotions": top_emotions,
                "analyzed_at": analyzed_at,
            }
        ), 200

    except Exception as e:  
        print("❌ Error fetching analysis:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Failed to fetch analysis: {str(e)}"}), 500