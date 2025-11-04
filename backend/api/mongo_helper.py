"""
MongoDB Helper Module
Provides utility functions and base class for MongoDB operations
"""
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional


def get_collection(collection_name: str):
    """Get MongoDB collection"""
    from interview_scheduler.settings import mongodb
    if not mongodb:
        raise Exception("MongoDB not connected. Check MONGODB_URI in .env")
    return mongodb[collection_name]


def serialize_doc(doc: Dict) -> Dict:
    """Convert MongoDB document to JSON-serializable dict"""
    if not doc:
        return None
    if '_id' in doc and isinstance(doc['_id'], ObjectId):
        doc['_id'] = str(doc['_id'])
    return doc


def serialize_docs(docs: List[Dict]) -> List[Dict]:
    """Convert list of MongoDB documents to JSON-serializable"""
    return [serialize_doc(doc) for doc in docs]


class MongoModel:
    """Base class for MongoDB collections"""
    collection_name = None
    
    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection"""
        if not cls.collection_name:
            raise ValueError("collection_name must be defined")
        return get_collection(cls.collection_name)
    
    @classmethod
    def find_all(cls, filter_dict: Dict = None) -> List[Dict]:
        """Find all documents"""
        collection = cls.get_collection()
        docs = list(collection.find(filter_dict or {}))
        return serialize_docs(docs)
    
    @classmethod
    def find_by_id(cls, id: str) -> Optional[Dict]:
        """Find document by ID"""
        try:
            collection = cls.get_collection()
            doc = collection.find_one({"_id": ObjectId(id)})
            return serialize_doc(doc)
        except Exception:
            return None
    
    @classmethod
    def find_one(cls, filter_dict: Dict) -> Optional[Dict]:
        """Find one document by filter"""
        collection = cls.get_collection()
        doc = collection.find_one(filter_dict)
        return serialize_doc(doc)
    
    @classmethod
    def create(cls, data: Dict) -> str:
        """Create new document"""
        collection = cls.get_collection()
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(data)
        return str(result.inserted_id)
    
    @classmethod
    def bulk_create(cls, data_list: List[Dict]) -> List[str]:
        """Create multiple documents"""
        collection = cls.get_collection()
        now = datetime.utcnow()
        for data in data_list:
            data['created_at'] = now
            data['updated_at'] = now
        result = collection.insert_many(data_list)
        return [str(id) for id in result.inserted_ids]
    
    @classmethod
    def update(cls, id: str, data: Dict) -> bool:
        """Update document by ID"""
        try:
            collection = cls.get_collection()
            data['updated_at'] = datetime.utcnow()
            result = collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    @classmethod
    def delete(cls, id: str) -> bool:
        """Delete document by ID"""
        try:
            collection = cls.get_collection()
            result = collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    @classmethod
    def count(cls, filter_dict: Dict = None) -> int:
        """Count documents"""
        collection = cls.get_collection()
        return collection.count_documents(filter_dict or {})
