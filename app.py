# Import necessary modules for creating a Flask application with MongoDB
from flask import request, jsonify
from bson import ObjectId
from database import create_app
import logging

# Set up logging for tracking application operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Flask application and MongoDB database from the database module
app = create_app()
db = app.db

# List of collection names for which CRUD routes will be dynamically created
collection_names = ["shoes", "data_sheet", "suggestion", "store", "pinterest", "tag"]

def convert_object_ids(data):
    """
    Convert JSON fields with $oid to MongoDB ObjectId.
    
    This function processes incoming JSON data and ensures fields formatted as MongoDB ObjectIds
    (e.g., {"$oid": "some_id"}) are properly converted to ObjectId instances.

    Args:
        data (dict or list): The JSON payload received in the request.

    Returns:
        dict or list: The data with ObjectId fields correctly converted.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) and "$oid" in value:
                try:
                    data[key] = ObjectId(value["$oid"])
                except Exception as e:
                    logger.error(f"Invalid ObjectId value for key '{key}': {value}. Error: {e}")
                    raise ValueError(f"Invalid ObjectId value for key '{key}': {value}")
            elif isinstance(value, (dict, list)):
                data[key] = convert_object_ids(value)
    elif isinstance(data, list):
        return [convert_object_ids(item) for item in data]
    return data

def create_crud_routes(collection_name):
    """
    Dynamically create CRUD routes for a specified MongoDB collection.
    
    This function generates standard CRUD operations (Create, Read, Update, Delete) for a collection.

    Args:
        collection_name (str): The name of the MongoDB collection for which to create routes.
    """
    collection = db[collection_name]  # Access the MongoDB collection

    @app.route(f'/{collection_name}', methods=['POST'], endpoint=f'create_{collection_name}')
    def create_document():
        """Handle POST requests to create a new document in the collection."""
        data = request.json
        if not data:
            logger.warning("No data provided in the request.")
            return jsonify({"error": "No data provided"}), 400
        
        try:
            data = convert_object_ids(data)  # Convert $oid fields to ObjectId
            result = collection.insert_one(data)
            logger.info(f"Document created in {collection_name} with ID: {result.inserted_id}")
            return jsonify({"message": "Document created", "id": str(result.inserted_id)}), 201
        except Exception as e:
            logger.error(f"Failed to create document in {collection_name}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route(f'/{collection_name}', methods=['GET'], endpoint=f'get_all_{collection_name}')
    def get_all_documents():
        """Handle GET requests to retrieve all documents from the collection."""
        try:
            documents = list(collection.find())
            for doc in documents:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string for JSON serialization
            logger.info(f"Retrieved all documents from {collection_name}")
            return jsonify(documents), 200
        except Exception as e:
            logger.error(f"Failed to retrieve documents from {collection_name}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route(f'/{collection_name}/<id>', methods=['GET'], endpoint=f'get_one_{collection_name}')
    def get_document(id):
        """Handle GET requests to retrieve a single document by ID."""
        try:
            document = collection.find_one({"_id": ObjectId(id)})
            if not document:
                logger.warning(f"Document with ID {id} not found in {collection_name}.")
                return jsonify({"error": "Document not found"}), 404
            document['_id'] = str(document['_id'])
            logger.info(f"Retrieved document with ID {id} from {collection_name}")
            return jsonify(document), 200
        except Exception as e:
            logger.error(f"Failed to retrieve document from {collection_name}: {e}")
            return jsonify({"error": str(e)}), 400

    @app.route(f'/{collection_name}/<id>', methods=['PUT'], endpoint=f'update_{collection_name}')
    def update_document(id):
        """Handle PUT requests to update a document by ID."""
        data = request.json
        if not data:
            logger.warning("No data provided in the request.")
            return jsonify({"error": "No data provided"}), 400
        
        try:
            result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
            if result.matched_count == 0:
                logger.warning(f"Document with ID {id} not found in {collection_name}.")
                return jsonify({"error": "Document not found"}), 404
            logger.info(f"Updated document with ID {id} in {collection_name}")
            return jsonify({"message": "Document updated"}), 200
        except Exception as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route(f'/{collection_name}/<id>', methods=['DELETE'], endpoint=f'delete_{collection_name}')
    def delete_document(id):
        """Handle DELETE requests to remove a document by ID."""
        try:
            result = collection.delete_one({"_id": ObjectId(id)})
            if result.deleted_count == 0:
                logger.warning(f"Document with ID {id} not found in {collection_name}.")
                return jsonify({"error": "Document not found"}), 404
            logger.info(f"Deleted document with ID {id} from {collection_name}")
            return jsonify({"message": "Document deleted"}), 200
        except Exception as e:
            logger.error(f"Failed to delete document from {collection_name}: {e}")
            return jsonify({"error": str(e)}), 500

# Dynamically create CRUD routes for all specified collections
for collection_name in collection_names:
    create_crud_routes(collection_name)

if __name__ == "__main__":
    # Run the Flask application
    logger.info("Starting Flask application...")
    app.run(debug=False)
