"""
MongoDB Helper Module
Provides utility functions and base class for MongoDB operations
"""
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
from .tenant import get_current_tenant, get_current_user


def get_collection(collection_name: str):
    """Get MongoDB collection"""
    from interview_scheduler.settings import mongodb
    if mongodb is None:
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
    def find_all(cls, filter_dict: Dict = None, limit: int = None, sort: List = None, company_id: Optional[str] = None) -> List[Dict]:
        """Find all documents with optional limit and sort.

        This method will automatically scope queries by `company_id` if a
        tenant is present in thread-local context or if `company_id` is
        explicitly provided.
        """
        collection = cls.get_collection()
        f = dict(filter_dict or {})
        cid = company_id or get_current_tenant()
        if cid:
            f.setdefault('company_id', cid)

        cursor = collection.find(f)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        docs = list(cursor)
        return serialize_docs(docs)
    
    @classmethod
    def find_by_id(cls, id: str, company_id: Optional[str] = None) -> Optional[Dict]:
        """Find document by ID and enforce tenant scoping.

        If `company_id` is provided or present in request context, it will be
        added to the query to avoid cross-tenant leaks.
        """
        try:
            collection = cls.get_collection()
            query = {"_id": ObjectId(id)}
            cid = company_id or get_current_tenant()
            if cid:
                query['company_id'] = cid
            doc = collection.find_one(query)
            return serialize_doc(doc)
        except Exception:
            return None
    
    @classmethod
    def find_one(cls, filter_dict: Dict, company_id: Optional[str] = None) -> Optional[Dict]:
        """Find one document by filter and enforce tenant scoping."""
        collection = cls.get_collection()
        f = dict(filter_dict or {})
        cid = company_id or get_current_tenant()
        if cid:
            f.setdefault('company_id', cid)
        doc = collection.find_one(f)
        return serialize_doc(doc)
    
    @classmethod
    def create(cls, data: Dict, company_id: Optional[str] = None, actor: Optional[Dict] = None) -> str:
        """Create new document.

        This enforces that `company_id` exists either in `data` or from the
        request tenant context. It also writes `created_at`/`updated_at` and
        emits an ActionLog entry for auditing.
        """
        collection = cls.get_collection()
        cid = company_id or get_current_tenant()
        if cid:
            data['company_id'] = cid
        if 'company_id' not in data or not data['company_id']:
            raise ValueError('company_id is required for create')
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(data)
        # audit (avoid recursion when creating action_logs themselves)
        try:
            if cls.collection_name != 'action_logs':
                actor = actor or get_current_user()
                from .mongo_models import ActionLog
                # write audit entry directly to collection to avoid nested audit calls
                try:
                    coll = ActionLog.get_collection()
                    audit_doc = {
                        'action_type': 'CREATE',
                        'resource_type': cls.collection_name,
                        'resource_id': str(result.inserted_id),
                        'company_id': data.get('company_id'),
                        'details': {'data_keys': list(data.keys())},
                        'created_at': datetime.utcnow()
                    }
                    coll.insert_one(audit_doc)
                except Exception:
                    # fallback to model create if direct insert fails (best-effort)
                    try:
                        ActionLog.create({'action_type': 'CREATE', 'resource_type': cls.collection_name, 'resource_id': str(result.inserted_id), 'company_id': data.get('company_id'), 'details': {'data_keys': list(data.keys())}})
                    except Exception:
                        pass
        except Exception:
            pass
        return str(result.inserted_id)
    
    @classmethod
    def bulk_create(cls, data_list: List[Dict], company_id: Optional[str] = None) -> List[str]:
        collection = cls.get_collection()
        now = datetime.utcnow()
        cid = company_id or get_current_tenant()
        for data in data_list:
            if cid:
                data['company_id'] = cid
            data['created_at'] = now
            data['updated_at'] = now
        result = collection.insert_many(data_list)
        # audit: create one log entry summarizing batch
        try:
            from .mongo_models import ActionLog
            ActionLog.create({'action_type': 'BULK_CREATE', 'resource_type': cls.collection_name, 'company_id': cid, 'details': {'count': len(data_list)}})
        except Exception:
            pass
        return [str(id) for id in result.inserted_ids]
    
    @classmethod
    def update(cls, id: str, data: Dict, company_id: Optional[str] = None) -> bool:
        """Update document by ID with tenant enforcement."""
        try:
            collection = cls.get_collection()
            cid = company_id or get_current_tenant()
            query = {"_id": ObjectId(id)}
            if cid:
                query['company_id'] = cid
            data['updated_at'] = datetime.utcnow()
            result = collection.update_one(query, {"$set": data})
            try:
                from .mongo_models import ActionLog
                ActionLog.create({'action_type': 'UPDATE', 'resource_type': cls.collection_name, 'resource_id': id, 'company_id': cid, 'details': {'updated_keys': list(data.keys())}})
            except Exception:
                pass
            return result.modified_count > 0
        except Exception:
            return False
    
    @classmethod
    def delete(cls, id: str, company_id: Optional[str] = None) -> bool:
        """Delete document by ID with tenant enforcement and audit."""
        try:
            collection = cls.get_collection()
            cid = company_id or get_current_tenant()
            query = {"_id": ObjectId(id)}
            if cid:
                query['company_id'] = cid
            result = collection.delete_one(query)
            try:
                from .mongo_models import ActionLog
                ActionLog.create({'action_type': 'DELETE', 'resource_type': cls.collection_name, 'resource_id': id, 'company_id': cid})
            except Exception:
                pass
            return result.deleted_count > 0
        except Exception:
            return False
    
    @classmethod
    def count(cls, filter_dict: Dict = None, company_id: Optional[str] = None) -> int:
        collection = cls.get_collection()
        f = dict(filter_dict or {})
        cid = company_id or get_current_tenant()
        if cid:
            f.setdefault('company_id', cid)
        return collection.count_documents(f)
    
    @classmethod
    def delete_all(cls, filter_dict: Dict = None, company_id: Optional[str] = None) -> int:
        collection = cls.get_collection()
        f = dict(filter_dict or {})
        cid = company_id or get_current_tenant()
        if cid:
            f.setdefault('company_id', cid)
        result = collection.delete_many(f)
        try:
            from .mongo_models import ActionLog
            ActionLog.create({'action_type': 'DELETE_ALL', 'resource_type': cls.collection_name, 'company_id': cid, 'details': {'filter': list(f.keys())}})
        except Exception:
            pass
        return result.deleted_count
