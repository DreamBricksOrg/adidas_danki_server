import os
import requests
from bs4 import BeautifulSoup
import boto3
from pymongo import MongoClient
from bson import ObjectId
import logging
import shutil  # Adicione essa importação

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do MongoDB
MONGO_URI = "mongodb+srv://guilhermebegotti:n5BHAuwiY1j3FxaF@dbcluster0.qkxkj.mongodb.net/?retryWrites=true&w=majority&appName=DBCluster0"
DB_NAME = "danki-adidas"
COLLECTION_NAME = "pinterest"

# Configurações do S3
S3_BUCKET_NAME = "dankiadidas"
S3_FOLDER_PREFIX = "PINTEREST_IMAGES/"

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

# Inicializa cliente S3
s3_client = boto3.client("s3")

# Inicializa cliente MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
pinterest_collection = db[COLLECTION_NAME]


def scrape_pinterest(board_url, output_folder):
    """
    Faz o scraping de imagens de um board do Pinterest.

    Args:
        board_url (str): URL do board do Pinterest.
        output_folder (str): Caminho para salvar as imagens localmente.

    Returns:
        list: Lista de caminhos para as imagens baixadas.
    """
    logger.info(f"Fazendo scraping do board: {board_url}")
    try:
        response = requests.get(board_url)
        soup = BeautifulSoup(response.content, "html.parser")
        image_tags = soup.find_all("img")
        
        image_paths = []
        for idx, img_tag in enumerate(image_tags):
            if "src" in img_tag.attrs:
                image_url = img_tag["src"]
                local_image_path = os.path.join(output_folder, f"{idx + 1}.jpg")
                with open(local_image_path, "wb") as img_file:
                    img_file.write(requests.get(image_url).content)
                image_paths.append(local_image_path)
        logger.info(f"Scraping completo. Total de imagens baixadas: {len(image_paths)}")
        return image_paths
    except Exception as e:
        logger.error(f"Erro durante o scraping do board {board_url}: {e}")
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

def force_delete_folder(folder_path):
    """
    Força a exclusão de uma pasta e todos os seus conteúdos.
    """
    try:
        # Garante que todos os arquivos sejam liberados antes de remover
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                os.chmod(file_path, 0o777)  # Altera permissões do arquivo
                os.remove(file_path)       # Remove o arquivo
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.chmod(dir_path, 0o777)  # Altera permissões da subpasta
                os.rmdir(dir_path)         # Remove a subpasta
        os.rmdir(folder_path)  # Remove a pasta principal
    except Exception as e:
        logger.error(f"Erro ao forçar exclusão da pasta {folder_path}: {e}")


# Dentro da função process_pinterest_boards
def process_pinterest_boards():
    """
    Processa todos os boards do Pinterest, faz o upload das imagens para o S3 e salva no MongoDB.
    """
    for board_url, (folder_name, shoe_ids) in SHOE_MAPPING.items():
        logger.info(f"Processando board: {board_url}")

        # Cria pasta temporária
        local_folder = f"./temp/{folder_name}"
        os.makedirs(local_folder, exist_ok=True)

        # Faz o scraping das imagens
        image_paths = scrape_pinterest(board_url, local_folder)

        # Faz o upload das imagens para o S3
        uploaded_urls = upload_images_to_s3(image_paths, folder_name)

        # Salva os links no MongoDB
        for shoe_id in shoe_ids:
            save_to_mongo(shoe_id, uploaded_urls)

        # Limpa os arquivos locais
        for image_path in image_paths:
            try:
                os.remove(image_path)  # Remove arquivos individuais
            except Exception as e:
                logger.error(f"Erro ao remover arquivo {image_path}: {e}")
        
        # Remove a pasta temporária usando a função customizada
        try:
            force_delete_folder(local_folder)  # Garante exclusão mesmo com bloqueios
        except Exception as e:
            logger.error(f"Erro ao remover a pasta {local_folder}: {e}")

    logger.info("Processamento de boards do Pinterest concluído.")


if __name__ == "__main__":
    process_pinterest_boards()
