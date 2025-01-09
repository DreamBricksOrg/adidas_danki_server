# =======================================
# Library Imports
# =======================================

# Import necessary modules for creating a Flask application with MongoDB
from flask import request, jsonify
from bson import ObjectId
from bson.json_util import dumps
from database import apply_schemas
from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
import requests
from flask_cors import CORS

# =======================================
# Variables
# =======================================

# Set up logging for tracking application operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of collection names for which CRUD routes will be dynamically created
collections = ["shoes", "suggestion", "pinterest", "images" ,"tag"]


# =======================================
# Setup and App Configuration
# =======================================

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


# Initialize the Flask application and MongoDB database from the database module
app = create_app()
CORS(app)
db = app.db


# =======================================
# Auxiliary Methods
# =======================================

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


def fetch_pinterest_data(board_id, access_token):
    """
    Fetches media data from a Pinterest board using the Pinterest API.

    Args:
        board_id (str): The unique identifier of the Pinterest board.
        access_token (str): Access token to authenticate with the Pinterest API.

    Returns:
        dict: Media data from the board, including image URLs, or None if the request fails.
    """
    url = f"https://api.pinterest.com/v5/boards/{board_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        # Make the API request to fetch board data
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # Parse and return the media data
        data = response.json()
        return data.get("media", None)
    except requests.RequestException as e:
        # Log and return None if the request fails
        logger.error(f"Failed to fetch Pinterest data: {e}")
        return None


# =======================================
# Routes
# =======================================

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
for collection_name in collections:
    create_crud_routes(collection_name)


# Atualizações no pipeline de /shoes-with-images
@app.route('/shoes-with-images', methods=['GET'])
def get_shoes_with_images():
    """
    Aggregates data from the 'shoes' and 'images' collections
    to provide a combined view of shoes with their image links.

    Returns:
        JSON response with a list of shoes, each including its id, model, code, title, description, and image links.
    """
    logger.info("Starting aggregation of shoes with their image links.")
    try:
        shoes_collection = db['shoes']

        pipeline = [
            {
                "$lookup": {
                    "from": "images",
                    "localField": "_id",
                    "foreignField": "shoeId",
                    "as": "images"
                }
            },
            {
                "$project": {
                    "id": "$_id",
                    "model": 1,
                    "code": 1,
                    "images": {"$arrayElemAt": ["$images.links", 0]}
                }
            }
        ]

        results = list(shoes_collection.aggregate(pipeline))
        json_results = dumps(results)

        logger.info(f"Aggregation successful. Retrieved {len(results)} shoes.")
        return json_results, 200
    except Exception as e:
        logger.error(f"Failed to aggregate shoes with images: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500


# Atualizações no pipeline de /shoe-with-pinterest
@app.route('/shoe-with-pinterest', methods=['GET'])
def get_shoe_with_pinterest():
    """
    Retrieves a single shoe with its Pinterest links based on ObjectId, code, or model.
    """
    logger.info("Starting aggregation for a single shoe with Pinterest links.")
    try:
        shoes_collection = db['shoes']

        shoe_id = request.args.get('id')
        shoe_code = request.args.get('code')
        shoe_model = request.args.get('model')

        match_query = {}
        if shoe_id:
            match_query["_id"] = ObjectId(shoe_id)
        elif shoe_code:
            match_query["code"] = shoe_code
        elif shoe_model:
            match_query["model"] = shoe_model

        if not match_query:
            return jsonify({"error": "You must provide at least one of 'id', 'code', or 'model'."}), 400

        pipeline = [
            {"$match": match_query},
            {
                "$lookup": {
                    "from": "pinterest",
                    "localField": "_id",
                    "foreignField": "shoeId",
                    "as": "pinterest"
                }
            },
            {
                "$project": {
                    "id": "$_id",
                    "model": 1,
                    "code": 1,
                    "pinterest_links": "$pinterest.links"
                }
            }
        ]

        results = list(shoes_collection.aggregate(pipeline))
        if not results:
            return jsonify({"error": "Shoe not found or no Pinterest links available."}), 404

        json_results = dumps(results[0])
        logger.info(f"Aggregation successful for shoe: {results[0]['id']}")
        return json_results, 200
    except Exception as e:
        logger.error(f"Failed to retrieve shoe with Pinterest links: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500


@app.route('/shoe-details', methods=['GET'])
def get_shoe_details():
    """
    Retrieves detailed information about a single shoe based on its ID, model, or code.
    """
    logger.info("Starting aggregation for a single shoe's detailed information.")
    try:
        shoes_collection = db['shoes']
        images_collection = db['images']
        suggestions_collection = db['suggestion']
        pinterest_collection = db['pinterest']

        shoe_id = request.args.get('id')
        model = request.args.get('model')
        code = request.args.get('code')

        query = {}
        if shoe_id:
            query["_id"] = ObjectId(shoe_id)
        elif model:
            query["model"] = model
        elif code:
            query["code"] = code
        else:
            return jsonify({"error": "No valid query parameter provided (id, model, or code)."}), 400

        shoe_details = shoes_collection.find_one(query)
        if not shoe_details:
            return jsonify({"error": "Shoe not found with the given criteria."}), 404

        # Fetch related images
        images = list(images_collection.find({"shoeId": shoe_details['_id']}))
        image_links = [link for image in images for link in image['links']]  # Get all images link

        pinterest_images = list(pinterest_collection.find({"shoeId": shoe_details['_id']}))
        pinterest_links = [pinterest_link for pinterest_image in pinterest_images for pinterest_link in
                           pinterest_image['links']]

        # Fetch colors with image links
        color_details = []
        for color_id in shoe_details.get('colors', []):
            color = shoes_collection.find_one({"_id": color_id})
            if color:
                color_image = images_collection.find_one({"shoeId": color['_id']})
                if color_image and len(color_image['links']) > 1:
                    color_details.append({
                        "shoeId": str(color['_id']),
                        "image": color_image['links'][1],
                        "code": color.get('code'),
                        "model": color.get('model')
                    })

        # Fetch suggestions with image links
        suggestion_details = []
        suggestions = suggestions_collection.find_one({"shoeId": shoe_details['_id']})
        if suggestions:
            for suggested_id in suggestions.get('shoes', []):
                suggested_shoe = shoes_collection.find_one({"_id": suggested_id})
                if suggested_shoe:
                    suggested_image = images_collection.find_one({"shoeId": suggested_shoe['_id']})
                    if suggested_image and len(suggested_image['links']) > 1:
                        suggestion_details.append({
                            "shoeId": str(suggested_shoe['_id']),
                            "image": suggested_image['links'][0],
                            "code": suggested_shoe.get('code'),
                            "model": suggested_shoe.get('model')
                        })

        result = {
            "_id": str(shoe_details['_id']),
            "code": shoe_details.get('code'),
            "model": shoe_details.get('model'),
            "title": shoe_details.get('title'),
            "description": shoe_details.get('description'),
            "colors": color_details,
            "images": image_links,
            "pinterest": pinterest_links,
            "suggestion": suggestion_details
        }

        json_result = dumps(result)
        logger.info("Aggregation successful for the requested shoe.")
        return json_result, 200
    except Exception as e:
        logger.error(f"Failed to aggregate shoe details: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500


@app.route('/add-pinterest-data', methods=['POST'])
def add_pinterest_data():
    """
    API endpoint to add or update a Pinterest document for a specific shoe.

    The request must provide:
    - "board_id": Pinterest board ID (required)
    - "access_token": Pinterest API access token (required)
    - "shoe_id", "code", or "model": Identifies the shoe to link with Pinterest data.

    Returns:
        JSON response indicating success or failure.
    """
    payload = request.json
    board_id = payload.get("board_id")
    access_token = payload.get("access_token")
    shoe_id = payload.get("shoe_id")
    code = payload.get("code")
    model = payload.get("model")

    # Validate the required parameters
    if not (board_id and access_token):
        return jsonify({"error": "board_id and access_token are required"}), 400

    # Fetch media data from the Pinterest API
    media_data = fetch_pinterest_data(board_id, access_token)
    if not media_data:
        return jsonify({"error": "Failed to fetch Pinterest data"}), 500

    # Build the query to find the associated shoe
    query = {}
    if shoe_id:
        query["_id"] = ObjectId(shoe_id)
    elif code:
        query["code"] = code
    elif model:
        query["model"] = model
    else:
        return jsonify({"error": "Provide shoe_id, code, or model to identify the shoe"}), 400

    # Search for the shoe in the database
    shoe = db['shoes'].find_one(query)
    if not shoe:
        return jsonify({"error": "Shoe not found"}), 404

    # Prepare the Pinterest document to insert/update
    pinterest_document = {
        "Shoe": shoe["_id"],  # Link the Pinterest data to the shoe's ObjectId
        "links": [media_data["image_cover_url"]] + media_data.get("pin_thumbnail_urls", [])
    }

    try:
        # Update or insert the Pinterest document for the shoe
        result = db['pinterest'].update_one(
            {"Shoe": shoe["_id"]},  # Match by the shoe's ObjectId
            {"$set": pinterest_document},  # Update the document fields
            upsert=True  # Insert if no matching document is found
        )
        logger.info(f"Pinterest data added/updated for shoe {shoe['_id']}")
        return jsonify({"message": "Pinterest data added/updated successfully",
                        "result": str(result.upserted_id or shoe["_id"])}), 200
    except Exception as e:
        # Log and return an error response if the operation fails
        logger.error(f"Failed to add/update Pinterest data: {e}")
        return jsonify({"error": "Failed to add/update Pinterest data", "details": str(e)}), 500


@app.route('/tag-by-address', methods=['GET'])
def get_shoe_by_tag():
    """
    Retrieves the shoeId associated with a given tagAddress from the 'tag' collection.

    Query Parameters:
        tagAddress (str): The tag address used to find the associated shoeId.

    Returns:
        JSON response with the shoeId or an error message if not found.
    """
    logger.info("Fetching shoeId by tagAddress from 'tag' collection.")

    tag_address = request.args.get('tagAddress')

    if not tag_address:
        return jsonify({"error": "tagAddress is required"}), 400

    try:
        tag = db['tag'].find_one({"tagAddress": tag_address})

        if not tag:
            logger.warning(f"No tag found with tagAddress: {tag_address}")
            return jsonify({"error": "Tag not found"}), 404

        shoe_id = str(tag.get("shoeId"))
        logger.info(f"Shoe found with ID: {shoe_id} for tagAddress: {tag_address}")
        return jsonify({"shoeId": shoe_id}), 200

    except Exception as e:
        logger.error(f"Failed to fetch shoe by tagAddress: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500



# =======================================
# Main Function
# =======================================

if __name__ == "__main__":
    # Run the Flask application
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5050)
