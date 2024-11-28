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

# Set up logging for tracking application operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
db = app.db

# List of collection names for which CRUD routes will be dynamically created
collections = ["shoes", "data_sheet", "suggestion", "store", "pinterest", "tag", "images"]

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

@app.route('/shoes-with-images', methods=['GET'])
def get_shoes_with_images():
    """
    Aggregates data from the 'shoes' and 'images' collections 
    to provide a combined view of shoes with their image links.

    Returns:
        JSON response with a list of shoes, each including its id, model, code, and image links.
    """
    logger.info("Starting aggregation of shoes with their image links.")
    try:
        # Reference to the 'shoes' and 'images' collections
        shoes_collection = db['shoes']

        # Aggregation pipeline to join shoes with their respective images
        pipeline = [
            {
                "$lookup": {
                    "from": "images",           # Join with the 'images' collection
                    "localField": "_id",        # Match '_id' in 'shoes'
                    "foreignField": "Shoe",   # Match 'Shoe' in 'images'
                    "as": "images"             # Output array of images
                }
            },
            {
                "$project": {
                    "id": "$_id",              # Include the shoe ID
                    "model": 1,                # Include the model
                    "code": 1,                 # Include the code
                    "images": "$images.links"  # Include the image links
                }
            }
        ]

        # Execute the aggregation
        results = list(shoes_collection.aggregate(pipeline))

        # Serialize results with bson.json_util.dumps
        json_results = dumps(results)

        logger.info(f"Aggregation successful. Retrieved {len(json_results)} shoes.")
        return json_results, 200
    except Exception as e:
        logger.error(f"Failed to aggregate shoes with images: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500

@app.route('/shoe-with-pinterest', methods=['GET'])
def get_shoe_with_pinterest():
    """
    Retrieves a single shoe with its Pinterest link based on ObjectId, code, or model.
    
    Query Parameters:
        - id: The ObjectId of the shoe.
        - code: The code of the shoe.
        - model: The model of the shoe.
    
    Returns:
        JSON response with the shoe's id, model, code, and a single Pinterest link.
    """
    logger.info("Starting aggregation for a single shoe with its Pinterest link.")
    try:
        # Reference to the 'shoes' collection
        shoes_collection = db['shoes']

        # Retrieve query parameters
        shoe_id = request.args.get('id')
        shoe_code = request.args.get('code')
        shoe_model = request.args.get('model')

        # Build the match query dynamically
        match_query = {}
        if shoe_id:
            try:
                match_query['_id'] = ObjectId(shoe_id)
            except Exception as e:
                logger.error(f"Invalid ObjectId format: {shoe_id}. Error: {e}")
                return jsonify({"error": "Invalid ObjectId format"}), 400
        if shoe_code:
            match_query['code'] = shoe_code
        if shoe_model:
            match_query['model'] = shoe_model

        # Ensure at least one query parameter is provided
        if not match_query:
            return jsonify({"error": "You must provide at least one of 'id', 'code', or 'model'."}), 400

        # Aggregation pipeline
        pipeline = [
            {"$match": match_query},  # Match the shoe based on the query
            {
                "$lookup": {
                    "from": "pinterest",      # Join with the 'pinterest' collection
                    "localField": "_id",      # Match '_id' in 'shoes'
                    "foreignField": "Shoe",   # Match 'Shoe' in 'pinterest'
                    "as": "pinterest"         # Output array of Pinterest links
                }
            },
            {
                "$project": {
                    "id": "$_id",                   # Include the shoe ID
                    "model": 1,                     # Include the model
                    "code": 1,                      # Include the model
                    "pinterest": "$pinterest.links"  # Directly include the link from Pinterest
                }
            }
        ]

        # Execute the aggregation
        results = list(shoes_collection.aggregate(pipeline))

        if not results:
            return jsonify({"error": "Shoe not found or no Pinterest links available."}), 404

        # Convert results to JSON using bson.json_util.dumps
        json_results = dumps(results[0])

        logger.info(f"Aggregation successful for shoe: {results[0]['id']}")
        return json_results, 200

    except Exception as e:
        logger.error(f"Failed to retrieve shoe with Pinterest link: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500

@app.route('/shoe-details', methods=['GET'])
def get_shoe_details():
    """
    Retrieves detailed information about a single shoe based on its ID, model, or code.

    Query Parameters:
        - id: ObjectId of the shoe (as a string).
        - model: The model name of the shoe.
        - code: The code of the shoe.

    Returns:
        JSON response with detailed shoe information or an error message.
    """
    logger.info("Starting aggregation for a single shoe's detailed information.")
    try:
        # Reference to the 'shoes' collection
        shoes_collection = db['shoes']

        # Get query parameters
        shoe_id = request.args.get('id')
        model = request.args.get('model')
        code = request.args.get('code')

        # Build the filter for the query
        query = {}
        if shoe_id:
            try:
                query["_id"] = ObjectId(shoe_id)
            except Exception as e:
                return jsonify({"error": "Invalid ObjectId format for 'id'", "details": str(e)}), 400
        elif model:
            query["model"] = model
        elif code:
            query["code"] = code
        else:
            return jsonify({"error": "No valid query parameter provided (id, model, or code)."}), 400

        # Aggregation pipeline to join all related collections for a single shoe
        pipeline = [
            {"$match": query},  # Match the specific shoe
            {
                "$lookup": {
                    "from": "images",
                    "localField": "_id",
                    "foreignField": "Shoe",
                    "as": "images"
                }
            },
            {
                "$lookup": {
                    "from": "pinterest",
                    "localField": "_id",
                    "foreignField": "Shoe",
                    "as": "pinterest"
                }
            },
            {
                "$lookup": {
                    "from": "data_sheet",  # Collection to join
                    "let": { "shoeId": "$_id" },  # Define a variable for the current shoe's _id
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": { "$in": ["$$shoeId", "$Shoes"] }  # Check if shoeId is in the Shoes array
                            }
                        }
                    ],
                    "as": "data_sheet"  # Output field for matched documents
                }
            },
            {
                "$lookup": {
                    "from": "store",
                    "localField": "_id",
                    "foreignField": "Shoe",
                    "as": "store"
                }
            },
            {
                "$lookup": {
                    "from": "suggestion",  # Collection to join
                    "let": { "shoeId": "$_id" },  # Define a variable for the current shoe's _id
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": { "$in": ["$$shoeId", "$Shoes"] }  # Check if shoeId is in the Shoes array
                            }
                        }
                    ],
                    "as": "suggestion"  # Output field for matched documents
                }
            },
            {
                "$lookup": {
                    "from": "tag",
                    "localField": "_id",
                    "foreignField": "Shoes",
                    "as": "tags"
                }
            },
            {
                "$project": {
                    "id": "$_id",
                    "model": 1,
                    "code": 1,
                    "color": 1,
                    "collection": 1,
                    "images": "$images.links",
                    "pinterest": {
                        "$arrayElemAt": ["$pinterest.link", 0]
                    },
                    "data_sheet": {
                        "$arrayElemAt": ["$data_sheet", 0]
                    },
                    "store": {
                        "$arrayElemAt": ["$store.address", 0]
                    },
                    "suggestion": "$suggestion",
                    "tags": "$tags.tag_id"
                }
            }
        ]

        # Execute the aggregation
        results = list(shoes_collection.aggregate(pipeline))

        if not results:
            return jsonify({"error": "Shoe not found with the given criteria."}), 404

        # Serialize the single result with bson.json_util.dumps
        json_result = dumps(results[0])

        logger.info("Aggregation successful for the requested shoe.")
        return json_result, 200
    except Exception as e:
        logger.error(f"Failed to aggregate shoe details: {e}")
        return jsonify({"error": "Failed to retrieve data", "details": str(e)}), 500



# Dynamically create CRUD routes for all specified collections
for collection_name in collections:
    create_crud_routes(collection_name)

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
        return jsonify({"message": "Pinterest data added/updated successfully", "result": str(result.upserted_id or shoe["_id"])}), 200
    except Exception as e:
        # Log and return an error response if the operation fails
        logger.error(f"Failed to add/update Pinterest data: {e}")
        return jsonify({"error": "Failed to add/update Pinterest data", "details": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask application
    logger.info("Starting Flask application...")
    app.run(debug=True)
