from flask import request, jsonify, current_app
from flask_login import login_required, current_user
import os
import secrets
from werkzeug.utils import secure_filename
from app.ai import bp
from app.services.chatbot_service import get_chatbot_response
from app.services.ocr_service import perform_ocr
from app.services.verification_service import verify_medicine_image

@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json() or {}
    message = data.get("message")
    history = data.get("history", [])
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
        
    response = get_chatbot_response(message, history)
    return jsonify({"response": response})

@bp.route('/ocr', methods=['POST'])
@login_required
def ocr_prescription():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    filename = secure_filename(file.filename)
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_ocr')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"ocr_{secrets.token_hex(4)}_{filename}")
    file.save(temp_path)
    
    try:
        results = perform_ocr(temp_path)
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": True, "medicines": results})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

@bp.route('/verify', methods=['POST'])
@login_required
def verify_pill():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    prescribed_name = request.form.get("prescribed_name")
    if not prescribed_name:
        return jsonify({"error": "Prescribed medicine name is required"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    filename = secure_filename(file.filename)
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_verify')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"verify_{secrets.token_hex(4)}_{filename}")
    file.save(temp_path)
    
    try:
        results = verify_medicine_image(temp_path, prescribed_name)
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify(results)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500
