from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
import json

# Set up logging to provide insights into the application's operation, both during development and after deployment
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_file):
    """
    Load a JSON schema from a file to enforce structure in MongoDB collections.
    
    Args:
        schema_file (str): Path to the JSON schema file.
    
    Returns:
        dict: The loaded schema as a dictionary.
    
    Raises:
        FileNotFoundError: If the JSON file could not be found.
        json.JSONDecodeError: If there is an error in decoding the JSON.
    """
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error(f"Schema file not found: {schema_file}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {schema_file}")
        raise e

def ensure_collection_exists(db, collection_name):
    """
    Ensures that a collection exists in the database before applying a schema validator.
    
    Args:
        db: The MongoDB database connection object.
        collection_name (str): The name of the collection to check or create.
    """
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        logger.info(f"Created new collection: {collection_name}")
    else:
        logger.info(f"Collection {collection_name} already exists.")

def apply_schemas(db):
    """
    Apply defined JSON schemas to MongoDB collections as validators to ensure data consistency.

    Args:
        db: The database connection object.
    """
    try:
        # Define schemas and their corresponding collections
        schemas = {
            "shoes": "schemas/shoes.json",
            "data_sheet": "schemas/dataSheet.json",
            "suggestion": "schemas/suggestion.json",
            "store": "schemas/store.json",
            "pinterest": "schemas/pinterest.json",
            "tag": "schemas/tag.json",
            "images": "schemas/images.json"
        }

        # Iterate over each collection and schema
        for collection, schema_path in schemas.items():
            # Ensure the collection exists
            ensure_collection_exists(db, collection)

            # Load and apply the schema
            schema = load_schema(schema_path)
            db.command('collMod', collection, validator={"$jsonSchema": schema})
            logger.info(f"{collection.capitalize()} schema applied successfully.")

    except Exception as e:
        logger.error(f"Failed to apply schemas: {str(e)}")
        raise


def create_app():
    """
    Create a Flask application and configure it with a MongoDB connection.
    
    Returns:
        Flask: The configured Flask application with a MongoDB connection.
    """
    app = Flask(__name__)
    # MongoDB URI configuration from environment or default setup
    app.config['MONGO_URI'] = "mongodb+srv://guilhermebegotti:n5BHAuwiY1j3FxaF@dbcluster0.qkxkj.mongodb.net/?retryWrites=true&w=majority&appName=DBCluster0"

    # Initialize MongoDB client
    mongo_client = MongoClient(app.config['MONGO_URI'], server_api=ServerApi('1'))
    try:
        # Test the MongoDB connection
        mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB successfully!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        mongo_client = None  # Set client to None if connection fails

    # Setup MongoDB in the Flask app context
    db = mongo_client['danki-adidas']
    apply_schemas(db)

    app.mongo_client = mongo_client
    app.db = db
    return app

# # This section is for running the Flask app
# if __name__ == "__main__":
#     app = create_app()
