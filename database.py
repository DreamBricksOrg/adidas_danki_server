from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging

def create_app():
    """
    Cria e configura uma instância do aplicativo Flask, incluindo a conexão com o MongoDB.
    
    Returns:
        Flask: A instância do aplicativo Flask configurada com uma conexão ao MongoDB.
    """
    # Inicializa uma nova aplicação Flask
    app = Flask(__name__)

    # Define a URI de conexão com o MongoDB obtida de configuração ou ambiente seguro
    app.config['MONGO_URI'] = "mongodb+srv://guilhermebegotti:n5BHAuwiY1j3FxaF@dbcluster0.qkxkj.mongodb.net/?retryWrites=true&w=majority&appName=DBCluster0"

    # Configuração do sistema de logging para registrar informações e erros
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Cria uma instância do cliente MongoDB com especificações de API de servidor para garantir compatibilidade
        mongo_client = MongoClient(app.config['MONGO_URI'], server_api=ServerApi('1'))
        # Realiza um comando de 'ping' para testar a conexão com o banco de dados
        mongo_client.admin.command('ping')
        # Registra no log a conexão bem-sucedida com o banco de dados
        logger.info("Connected to MongoDB successfully!")
    except Exception as e:
        # Registra no log o fracasso na tentativa de conexão, incluindo a mensagem de erro
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Define o cliente MongoDB como None se a conexão falhar
        mongo_client = None

    # Armazena o cliente MongoDB na aplicação para ser acessado por outras partes do aplicativo
    app.mongo_client = mongo_client
    return app

# # Uso típico para inicializar o aplicativo com acesso ao MongoDB configurado
# if __name__ == "__main__":
#     app = create_app()
#     # O aplicativo pode agora ser iniciado ou utilizado com um cliente MongoDB integrado
