from pymongo import MongoClient
from bson.objectid import ObjectId

def connect_to_mongodb(collection):
    client = MongoClient('localhost', 27017)
    db = client['KLTN']
    collection_name = db[collection]
    return collection_name, client

def connect_to_collection(collection, client):
    db = client['KLTN']
    collection_name = db[collection]
    return collection_name
def connect_to_client():
    client = MongoClient('localhost', 27017)
    return client

def close_mongodb_connection(client):
    client.close()

def save_person_to_mongodb(collection, bib, face, pictures):
    person_data = {
        'bib': bib,
        'face': face,
        'picture': pictures
    }
    collection.insert_one(person_data)

def get_all_documents(collection):
    documents = collection.find()
    return documents

def get_documents_by_condition(collection, condition):
    documents = collection.find(condition)
    return documents

def get_document(collection, condition):
    document = collection.find_one(condition)
    return document

def get_field_value(collection, condition, field):
    document = collection.find_one(condition)
    if document:
        value = document.get(field)
    return value

def find_similar_values(collection, field, value):
    condition = {field: {"$regex": value}}
    documents = collection.find(condition).sort([(field, -1)])
    return documents

def get_all_pictures(collection):
    documents = collection.find({}, {'picture': 1})
    return documents

def get_all_collections(client):
    db = client['KLTN']
    return db.list_collection_names()

#find_document_by_id
def find_document_by_id(collection, document_id):
    result = collection.find_one({'_id': ObjectId(document_id)})
    if result:
        return result
    else:
        return None
    