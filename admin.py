from flask import Blueprint, render_template, request, jsonify
import json
from utils.boto import upload_file_blob_to_s3
import os

admin = Blueprint('admin', __name__)

@admin.route('/')
def menu_page():
    return render_template('admin/menu.html')

@admin.route('/sneaker/list')
def sneaker_list_page():
    return render_template('admin/list-sneaker.html')

@admin.route('/sneaker/detail')
def sneaker_detail_page():
    from app import get_shoe_details
    sneaker_json = get_shoe_details()[0]
    sneaker = json.loads(sneaker_json)
    print(sneaker)
    return render_template('admin/detail-sneaker.html',sneaker=sneaker)

@admin.route('/sneaker/create')
def sneaker_create_page():
    return render_template('admin/create-sneaker.html')

@admin.route('/sneaker/scan-tag')
def scan_tag_page():
    return render_template('admin/scan-tag.html')

@admin.route("/sneaker/upload-file", methods=["POST"])
def upload_image():
    TEST_BUCKET = os.getenv("TEST_S3_BUCKET")
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nome do arquivo inválido"}), 400

    s3_key = f"uploads/{file.filename}"
    file_url = upload_file_blob_to_s3(file, TEST_BUCKET, s3_key)

    if file_url:
        return jsonify({"message": "Upload realizado com sucesso", "file_url": file_url}), 200
    else:
        return jsonify({"error": "Erro ao fazer upload"}), 500