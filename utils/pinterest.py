import os
import requests
import boto3
from pymongo import MongoClient
from bson import ObjectId
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Relacionamento entre os links, pastas e shoeId
SHOE_MAPPING = {
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-samba-og/": ("SAMBA_OG", ["674a2609f03d766411a9308b", "674a2609f03d766411a93095", "674a2609f03d766411a9309d"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-samba-og-w/": ("SAMBA_OG_W", ["674a2609f03d766411a93099"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-campus-00s/": ("CAMPUS_00S", ["674a2609f03d766411a930a1"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-gazelle/": ("GAZELLE", ["674a2609f03d766411a93097"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-gazelle-bold/": ("CAMPUS", ["674a2609f03d766411a93093"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-campus-00s-w/": ("CAMPUS_00S_W", ["674a2609f03d766411a9308f"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-sl-72-rs-j/": ("SL_72_RS_INFANTIL", ["674a2609f03d766411a93091"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-gazelle-indoor-w/": ("GAZELLE_INDOOR_W", ["674a2609f03d766411a9309f"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-gazelle-bold-w/": ("GAZELLE_BOLD_W", ["674a2609f03d766411a9309b"]),
    "https://br.pinterest.com/dankibrasil/t%C3%AAnis-gazelle-indoor/": ("GAZELLE_INDOOR", ["674a2609f03d766411a9308d"]),
}

# Configurações do S3
S3_BUCKET_NAME = "dankiadidas"
S3_FOLDER_PREFIX = "PINTEREST_IMAGES/"

# Inicializa cliente S3
s3_client = boto3.client("s3")

# Configurações do MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "danki-adidas"
COLLECTION_NAME = "pinterest"

# Inicializa cliente MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
pinterest_collection = db[COLLECTION_NAME]

PINTEREST_TOKEN=os.getenv("PINTEREST_TOKEN")

def get_pins(board_id, output_folder, shoe_ids):
    """
    Faz o scraping de imagens de um board do Pinterest.

    Args:
        board_id (str): Id do board do Pinterest.
        output_folder (str): Caminho para salvar as imagens localmente.

    Returns:
        list: Lista de caminhos para as imagens baixadas.
    """
    logger.info(f"Baixando imagens do board {board_id} pela API")
    try:
        os.makedirs(output_folder, exist_ok=True)

        headers = {
            'Authorization': f'Bearer {PINTEREST_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.get(
            f'https://api.pinterest.com/v5/boards/{board_id}/pins?board_id={board_id}',
            headers=headers
        )
        response.raise_for_status()  # Garante que erro de status HTTP seja tratado

        data = response.json()
        pins_data = data.get("items", [])

        image_paths = []

        for idx, pin in enumerate(pins_data):
            try:
                image_url = pin.get("media", {}).get("images", {}).get("1200x", {}).get("url")
                if image_url:
                    local_image_path = os.path.join(output_folder, f"{shoe_ids}-{idx}.jpg")
                    img_response = requests.get(image_url)
                    img_response.raise_for_status()
                    with open(local_image_path, "wb") as img_file:
                        img_file.write(img_response.content)
                    image_paths.append(local_image_path)
                else:
                    logger.warning(f"Imagem não encontrada no pin {pin.get('id')}")
            except Exception as inner_e:
                logger.error(f"Erro ao baixar imagem do pin {pin.get('id')}: {inner_e}")

        logger.info(f"Download completo. Total de imagens baixadas: {len(image_paths)}")
        return image_paths

    except Exception as e:
        logger.error(f"Erro durante o dowalod dos pins do board {board_id}: {e}")
        return []


def upload_images_to_s3(image_paths, folder_name):
    """
    Faz o upload de imagens para o bucket S3.

    Args:
        image_paths (list): Lista de caminhos para as imagens locais.
        folder_name (str): Nome da pasta no bucket S3.

    Returns:
        list: Lista de URLs das imagens no bucket S3.
    """
    uploaded_urls = []
    for image_path in image_paths:
        try:
            s3_key = f"{S3_FOLDER_PREFIX}{folder_name}/{os.path.basename(image_path)}"
            s3_client.upload_file(image_path, S3_BUCKET_NAME, s3_key)
            uploaded_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
            uploaded_urls.append(uploaded_url)
        except Exception as e:
            logger.error(f"Erro ao fazer upload da imagem {image_path} para o S3: {e}")
    return uploaded_urls


def save_to_mongo(shoe_id, image_links):
    """
    Salva ou atualiza documentos no MongoDB.

    Args:
        shoe_id (str): ID do tênis na coleção shoes.
        image_links (list): Lista de links de imagens.
    """
    document = {
        "shoeId": ObjectId(shoe_id),
        "links": image_links,
    }
    try:
        pinterest_collection.update_one(
            {"shoeId": ObjectId(shoe_id)},
            {"$set": document},
            upsert=True
        )
        logger.info(f"Documento salvo para shoeId: {shoe_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar documento no MongoDB para shoeId {shoe_id}: {e}")


def process_pinterest_boards(board_id, folder_name, shoe_ids):
    """
    Processa todos os boards do Pinterest, faz o upload das imagens para o S3 e salva no MongoDB.
    """
    logger.info(f"Processando board: {board_id}")

    # Cria pasta temporária
    local_folder = f"./temp/{folder_name}"
    os.makedirs(local_folder, exist_ok=True)

    # Salva os links no MongoDB
    for shoe_id in shoe_ids:
        # Faz o scraping das imagens
        image_paths = get_pins(board_id, local_folder, shoe_id)

        # Faz o upload das imagens para o S3
        uploaded_urls = upload_images_to_s3(image_paths, folder_name)
        
        save_to_mongo(shoe_id, uploaded_urls)

    # Limpa os arquivos locais
    for image_path in image_paths:
        try:
            os.remove(image_path)  # Remove arquivos individuais
        except Exception as e:
            logger.error(f"Erro ao remover arquivo {image_path}: {e}")
    
    # Remove a pasta temporária, mas sem afetar pastas no S3
    try:
        os.rmdir(local_folder)
    except Exception as e:
        logger.error(f"Erro ao remover a pasta {local_folder}: {e}")

    logger.info("Processamento de boards do Pinterest concluído.")
