# models/document_mysql.py
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from enum import Enum
from users import MySQLDatabase
import json

class DocumentType(str, Enum):
    INVOICE = "invoice"
    RESUME = "resume"
    FORM = "form"
    LETTER = "letter"
    NEWS_ARTICLE = "news_article"
    EMAIL = "email"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentCreate(BaseModel):
    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    summary: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    folder_id: Optional[str]
    original_filename: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    summary: Optional[str]
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

class FolderCreate(BaseModel):
    name: str

class FolderResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime

class SearchFilters(BaseModel):
    document_type: Optional[DocumentType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    folder_id: Optional[str] = None
    query: Optional[str] = None

class DocumentManager:
    def __init__(self, db_connection: MySQLDatabase):
        self.db = db_connection

    def create_document(self, user_id: str, document_data: DocumentCreate, 
                       folder_id: Optional[str] = None) -> Optional[DocumentResponse]:
        """Store processed document in database"""
        document_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO processed_documents 
        (id, user_id, folder_id, original_filename, file_path, file_size, mime_type,
         document_type, extracted_data, summary, confidence_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self.db.execute_query(
            query,
            (document_id, user_id, folder_id, document_data.original_filename, 
             document_data.file_path, document_data.file_size,
             document_data.mime_type, document_data.document_type.value,
             json.dumps(document_data.extracted_data), document_data.summary
             ),
            fetch=False
        )
        
        # Get the created document
        return self.get_document(document_id, user_id) 

    def get_document(self, document_id: str, user_id: str) -> Optional[DocumentResponse]:
        """Get document by ID for specific user"""
        query = """
        SELECT * FROM processed_documents 
        WHERE id = %s AND user_id = %s
        """
        
        result = self.db.execute_query(query, (document_id, user_id))
        
        if not result:
            return None
        
        doc:dict = result[0]
        if doc['extracted_data'] and isinstance(doc['extracted_data'], str):
            doc['extracted_data'] = json.loads(doc['extracted_data'])
            
        return DocumentResponse(**doc)

    def get_user_documents(self, user_id: str, limit: int = 50, 
                          offset: int = 0) -> List[DocumentResponse]:
        """Get all documents for a user"""
        query = """
        SELECT * FROM processed_documents 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
        """
        
        result = self.db.execute_query(query, (user_id, limit, offset))
        
        documents = []
        for doc in result:
            if doc['extracted_data'] and isinstance(doc['extracted_data'], str):
                doc['extracted_data'] = json.loads(doc['extracted_data'])
            documents.append(DocumentResponse(**doc))
        
        return documents

    def search_documents(self, user_id: str, filters: SearchFilters, 
                        limit: int = 50, offset: int = 0) -> List[DocumentResponse]:
        """Search documents with filters"""
        base_query = """
        SELECT * FROM processed_documents 
        WHERE user_id = %s
        """
        params = [user_id]
        
        conditions = []
        
        if filters.document_type:
            conditions.append("document_type = %s")
            params.append(filters.document_type.value)
            
        if filters.date_from:
            conditions.append("created_at >= %s")
            params.append(filters.date_from.strftime('%Y-%m-%d %H:%M:%S'))
            
        if filters.date_to:
            conditions.append("created_at <= %s")
            params.append(filters.date_to.strftime('%Y-%m-%d %H:%M:%S'))
                  
        if filters.folder_id:
            conditions.append("folder_id = %s")
            params.append(filters.folder_id)
            
        if filters.query:
            conditions.append("""
            (original_filename LIKE %s OR 
             summary LIKE %s OR
             extracted_data LIKE %s)
            """)
            search_term = f"%{filters.query}%"
            params.extend([search_term, search_term, search_term])
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([str(limit), str(offset)])
        
        result = self.db.execute_query(base_query, tuple(params))
        
        documents = []
        for doc in result:
            if doc['extracted_data'] and isinstance(doc['extracted_data'], str):
                doc['extracted_data'] = json.loads(doc['extracted_data'])
            documents.append(DocumentResponse(**doc))
        
        return documents

    def update_document_folder(self, document_id: str, user_id: str, 
                              folder_id: Optional[str]) -> bool:
        """Move document to different folder"""
        query = """
        UPDATE processed_documents 
        SET folder_id = %s
        WHERE id = %s AND user_id = %s
        """
        
        result = self.db.execute_query(
            query, 
            (folder_id, document_id, user_id),
            fetch=False
        )
        
        # Check if any row was affected
        check_query = "SELECT 1 FROM processed_documents WHERE id = %s AND user_id = %s AND folder_id = %s"
        result = self.db.execute_query(check_query)
        return bool(result)

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document"""
        query = "DELETE FROM processed_documents WHERE id = %s AND user_id = %s"
        self.db.execute_query(query, (document_id, user_id), fetch=False)
        
        # Check if any row was affected
        check_query =  "SELECT 1 FROM processed_documents WHERE id = %s AND user_id = %s"
        result = self.db.execute_query(check_query)
        return not bool(result) 
