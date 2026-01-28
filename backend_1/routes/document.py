# routes/documents_mysql.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from models.document import (
    DocumentCreate, DocumentResponse, FolderCreate, FolderResponse,
    SearchFilters, DocumentType, ProcessingStatus, DocumentManager
)
from models.users import MySQLDatabase
from models.folder import FolderManager
from auth.auth_services import AuthService
from routes.auth_routes import get_session_token,get_auth_service

router = APIRouter(prefix="/documents", tags=["documents"])

def get_db():
    db = MySQLDatabase()
    db.connect()
    try:
        yield db
    finally:
        db.close()

def get_document_manager(db=Depends(get_db)) -> DocumentManager:
    return DocumentManager(db)

def get_folder_manager(db=Depends(get_db)) -> FolderManager:
    return FolderManager(db)

@router.post("/upload")
async def upload_document(
    document_data: DocumentCreate,
    folder_id: Optional[str] = None,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    doc_manager: DocumentManager = Depends(get_document_manager)
):
    """Store a processed document"""
    user = auth_service.get_current_user(session_token)
    
    document = doc_manager.create_document(
        user.id, document_data, folder_id
    )
    
    return {
        "document": document,
        "message": "Document stored successfully"
    }

@router.get("/")
async def get_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    doc_manager: DocumentManager = Depends(get_document_manager)
):
    """Get user's documents"""
    user = auth_service.get_current_user(session_token)
    documents = doc_manager.get_user_documents(user.id, limit, offset)
    
    return {
        "documents": documents,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(documents)
        }
    }

@router.post("/search")
async def search_documents(
    filters: SearchFilters,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    doc_manager: DocumentManager = Depends(get_document_manager)
):
    """Search documents with filters"""
    user = auth_service.get_current_user(session_token)
    documents = doc_manager.search_documents(user.id, filters, limit, offset)
    
    return {
        "documents": documents,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(documents)
        }
    }


@router.put("/{document_id}/folder")
async def move_document(
    document_id: str,
    folder_id: Optional[str] = None,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    doc_manager: DocumentManager = Depends(get_document_manager)
):
    """Move document to different folder"""
    user = auth_service.get_current_user(session_token)
    
    success = doc_manager.update_document_folder(document_id, user.id, folder_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"message": "Document moved successfully"}

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    doc_manager: DocumentManager = Depends(get_document_manager)
):
    """Delete a document"""
    user = auth_service.get_current_user(session_token)
    
    success = doc_manager.delete_document(document_id, user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"message": "Document deleted successfully"}

@router.post("/folders")
async def create_folder(
    folder_data: FolderCreate,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    folder_manager: FolderManager = Depends(get_folder_manager)
):
    """Create a new folder"""
    user = auth_service.get_current_user(session_token)
    folder = folder_manager.create_folder(user.id, folder_data)
    
    return {
        "folder": folder,
        "message": "Folder created successfully"
    }

@router.get("/folders")
async def get_folders(
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    folder_manager: FolderManager = Depends(get_folder_manager)
):
    """Get user's folders"""
    user = auth_service.get_current_user(session_token)
    folders = folder_manager.get_user_folders(user.id)
    
    return {"folders": folders}


@router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: str,
    name: str,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    folder_manager: FolderManager = Depends(get_folder_manager)
):
    """Update folder name"""
    user = auth_service.get_current_user(session_token)
    folder = folder_manager.update_folder(folder_id, user.id, name)
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    return {
        "folder": folder,
        "message": "Folder updated successfully"
    }

@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    move_to_folder_id: Optional[str] = None,
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service),
    folder_manager: FolderManager = Depends(get_folder_manager)
):
    """Delete a folder"""
    user = auth_service.get_current_user(session_token)
    
    success = folder_manager.delete_folder(folder_id, user.id, move_to_folder_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    return {"message": "Folder deleted successfully"}