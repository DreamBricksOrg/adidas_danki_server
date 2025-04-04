from flask import Blueprint, render_template, request, jsonify
import json
from utils.boto import upload_file_blob_to_s3
import os
import random
import requests

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
    return render_template('admin/detail-sneaker.html', sneaker=sneaker)


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

    # Validação dos argumentos
    sneaker_name = request.form.get("sneaker_name")
    sneaker_sku = request.form.get("sneaker_sku")

    if not sneaker_name or not sneaker_sku:
        return jsonify({"error": "Parâmetros 'sneaker_name' e 'sneaker_sku' são obrigatórios"}), 400

    # Pegando extensão do arquivo (ex: '.jpg', '.png', etc.)
    _, file_extension = os.path.splitext(file.filename)

    # Geração de código aleatório e criação da key com extensão
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    s3_key = f"{sneaker_name}/{sneaker_sku}_{code}{file_extension}"

    # Upload para o S3
    file_url = upload_file_blob_to_s3(file, TEST_BUCKET, s3_key)

    if file_url:
        return jsonify({"message": "Upload realizado com sucesso", "file_url": file_url}), 200
    else:
        return jsonify({"error": "Erro ao fazer upload"}), 500


@admin.route('/pinterest/boards', methods=['GET'])
def get_pinterest_boards():
    PINTEREST_TOKEN = os.getenv("PINTEREST_TOKEN")
    url = "https://api.pinterest.com/v5/boards"
    headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se o status code for 4xx ou 5xx
        data = response.json()

        boards = []
        for board in data.get('items', []):
            board_info = {
                "id": board.get("id"),
                "name": board.get("name"),
                "image_cover_url": board.get("media", {}).get("image_cover_url", "")
            }
            boards.append(board_info)

        return jsonify({"items": boards}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
