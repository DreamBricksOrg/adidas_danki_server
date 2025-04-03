import json
from pymongo import MongoClient

# Conectar ao MongoDB
client = MongoClient("mongodb+srv://guilhermebegotti:n5BHAuwiY1j3FxaF@dbcluster0.qkxkj.mongodb.net/?retryWrites=true&w=majority&appName=DBCluster0")
db = client["danki-adidas"]
shoes_collection = db["shoes"]
images_collection = db["images"]

# Caminho para o arquivo JSON
file_path = 'import.json'

# Carregar dados do arquivo JSON
with open(file_path, 'r', encoding='utf-8') as file:
    shoes_data = json.load(file)

# Inserir dados na coleção 'shoes' e criar documentos de imagens
for shoe in shoes_data:
    # Extração das imagens
    images = [shoe.pop(key) for key in ["image_1", "image_2", "image_3"] if key in shoe]

    # Inserir dados do tênis
    inserted_shoe = shoes_collection.insert_one(shoe)
    shoe_id = inserted_shoe.inserted_id

    # Criar documento de imagens
    images_document = {
        "shoeId": shoe_id,
        "links": images
    }
    images_collection.insert_one(images_document)

    print(f'Successfully inserted shoe {shoe["model"]} with images.')

print("All data has been imported to MongoDB.")
