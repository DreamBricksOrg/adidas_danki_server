import json
from pymongo import MongoClient
from bson import ObjectId

# Configurar conexão com o MongoDB
client = MongoClient("mongodb+srv://guilhermebegotti:n5BHAuwiY1j3FxaF@dbcluster0.qkxkj.mongodb.net/?retryWrites=true&w=majority&appName=DBCluster0")
db = client["danki-adidas"]
suggestion_collection = db["suggestion"]

# Caminho do arquivo JSON modificado
file_path = "import_suggestion.json"  # Atualize com o caminho correto

# Carregar os dados do arquivo
with open(file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# Inserir documentos um por um convertendo os ObjectId corretamente
inserted_count = 0
for item in data:
    try:
        # Corrigir o formato do shoeId e dos shoes
        item["shoeId"] = ObjectId(item["shoeId"]["$oid"])
        item["shoes"] = [ObjectId(shoe["$oid"]) for shoe in item["shoes"]]

        # Inserir no MongoDB
        suggestion_collection.insert_one(item)
        inserted_count += 1
        print(f"Documento inserido: {item['shoeId']}")

    except Exception as e:
        print(f"Erro ao inserir documento {item['shoeId']}: {e}")

print(f"\nImportação concluída! {inserted_count} documentos inseridos com sucesso.")
