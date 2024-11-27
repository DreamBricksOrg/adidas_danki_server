# API Documentation

## CRUD Endpoints for Dynamic Collections

Base Path: `/`
Collections: `shoes`, `data_sheet`, `suggestion`, `store`, `pinterest`, `tag`, `images`

### Create a Document

- **Method**: POST
- **Endpoint**: `/<collection_name>`
- **Request Body**:

    ```json
    {
        "field1": "value",
        "field2": "value"
    }
    ```

- **Response**:
- Success: `201 Created`
        ```json
        {
            "message": "Document created",
            "id": "ObjectId of the created document"
        }
        ```
- Error: `400 Bad Request`
        ```json
        {
            "error": "No data provided"
        }
        ```

### Get All Documents

- **Method**: GET
- **Endpoint**: `/<collection_name>`
- **Response**:
- Success: `200 OK`
        ```json
        [
            { "field1": "value1", "_id": "ObjectId1" },
            { "field2": "value2", "_id": "ObjectId2" }
        ]
        ```
- Error: `500 Internal Server Error`

### Get a Document by ID

- **Method**: GET
- **Endpoint**: `/<collection_name>/<id>`
- **Response**:
- Success: `200 OK`
        ```json
        {
            "field1": "value1",
            "_id": "ObjectId"
        }
        ```
- Error: `404 Not Found`

### Update a Document by ID

- **Method**: PUT
- **Endpoint**: `/<collection_name>/<id>`
- **Request Body**:

    ```json
    {
        "field1": "updated_value"
    }
    ```

- **Response**:
- Success: `200 OK`
        ```json
        {
            "message": "Document updated"
        }
        ```
- Error: `404 Not Found`

### Delete a Document by ID

- **Method**: DELETE
- **Endpoint**: `/<collection_name>/<id>`
- **Response**:
- Success: `200 OK`
        ```json
        {
            "message": "Document deleted"
        }
        ```
- Error: `404 Not Found`

## Aggregation Endpoints

### Shoes with Images

- **Method**: GET
- **Endpoint**: `/shoes-with-images`
- **Description**: Retrieves all shoes with their associated image links.
- **Response**:
- Success: `200 OK`
        ```json
        [
            {
                "id": "ObjectId",
                "model": "Shoe model",
                "code": "Shoe code",
                "images": ["image1.jpg", "image2.jpg"]
            }
        ]
        ```
- Error: `500 Internal Server Error`

### Shoe with Pinterest

- **Method**: GET
- **Endpoint**: `/shoe-with-pinterest`
- **Query Parameters**:
- `id` (optional): The ObjectId of the shoe.
- `code` (optional): The code of the shoe.
- `model` (optional): The model of the shoe.
- **Response**:
- Success: `200 OK`
        ```json
        {
            "id": "ObjectId",
            "model": "Shoe model",
            "code": "Shoe code",
            "pinterest": "Pinterest link"
        }
        ```
- Error: `400 Bad Request` or `404 Not Found`

### Shoe Details

- **Method**: GET
- **Endpoint**: `/shoe-details`
- **Query Parameters**:
- `id` (optional): The ObjectId of the shoe.
- `code` (optional): The code of the shoe.
- `model` (optional): The model of the shoe.
- **Response**:
- Success: `200 OK`
        ```json
        {
            "id": "ObjectId",
            "model": "Shoe model",
            "code": "Shoe code",
            "color": "Shoe color",
            "collection": "Collection name",
            "images": ["image1.jpg", "image2.jpg"],
            "pinterest": "Pinterest link",
            "data_sheet": { "field": "value" },
            "store": "Store address",
            "suggestion": [{ "id": "ObjectId" }],
            "tags": ["tag1", "tag2"]
        }
        ```
- Error: `400 Bad Request` or `404 Not Found`

## Instructions for Testing

1. Use Postman or cURL to make requests to the above endpoints.
2. Replace `<collection_name>` with the name of the collection you want to interact with (e.g., `shoes`, `pinterest`).
3. Ensure the MongoDB connection is running and the database is populated with the correct schema.
