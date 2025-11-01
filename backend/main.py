from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import uuid
import os
from datetime import datetime

# Import YOUR EXISTING MODULES
from backend.database import get_db, MySQLDatabase
from backend.models import User, DocumentManager, DocumentCreate
from backend.auth import AuthService, get_session_token

app = FastAPI(title="DocuMind AI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

# Initialize your existing services
db = MySQLDatabase()
db.connect()
document_manager = DocumentManager(db)
auth_service = AuthService(db)

# Simple session storage for demo (use your proper session management)
user_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        # Use YOUR existing authentication
        result = auth_service.login_user({
            "email": email,
            "password": password
        })
        
        # Create session (simplified - use your proper session management)
        session_id = str(uuid.uuid4())
        user_sessions[session_id] = {
            "user_id": result["user"]["id"],
            "email": result["user"]["email"],
            "session_token": result["session_token"]
        }
        
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_id", value=session_id)
        return response
        
    except HTTPException as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": e.detail
        })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in user_sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    user_data = user_sessions[session_id]
    
    # Get user's documents from YOUR MySQL database
    documents = document_manager.get_user_documents(user_data["user_id"], limit=10)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_data,
        "documents": documents
    })

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in user_sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "user": user_sessions[session_id]
    })

@app.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: Optional[str] = Form("auto")
):
    try:
        # Check authentication
        session_id = request.cookies.get("session_id")
        if not session_id or session_id not in user_sessions:
            return RedirectResponse(url="/login", status_code=303)
        
        user_data = user_sessions[session_id]
        user_id = user_data["user_id"]
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, saved_filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process with YOUR existing AI engine
        processing_result = await process_with_your_ai(file_path, file.filename, document_type)
        
        # Save to YOUR MySQL database using existing DocumentManager
        document_data = DocumentCreate(
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            document_type=processing_result["document_type"],
            extracted_data=processing_result["extracted_data"],
            summary=processing_result["summary"],
            confidence_score=processing_result["confidence_score"]
        )
        
        # Use YOUR existing document manager
        stored_document = document_manager.create_document(
            user_id, document_data
        )
        
        return RedirectResponse(url="/documents", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": f"Upload failed: {str(e)}"
        })

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in user_sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    user_data = user_sessions[session_id]
    
    # Get documents from YOUR MySQL database
    documents = document_manager.get_user_documents(user_data["user_id"])
    
    return templates.TemplateResponse("documents.html", {
        "request": request,
        "user": user_data,
        "documents": documents
    })

@app.get("/document/{document_id}", response_class=HTMLResponse)
async def view_document(request: Request, document_id: str):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in user_sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    user_data = user_sessions[session_id]
    
    # Get document from YOUR MySQL database
    document = document_manager.get_document(document_id, user_data["user_id"])
    
    if not document:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Document not found"
        })
    
    return templates.TemplateResponse("document_detail.html", {
        "request": request,
        "user": user_data,
        "document": document
    })

@app.post("/delete/{document_id}")
async def delete_document(document_id: str, request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in user_sessions:
        return RedirectResponse(url="/login", status_code=303)
    
    user_data = user_sessions[session_id]
    
    # Delete using YOUR existing document manager
    success = document_manager.delete_document(document_id, user_data["user_id"])
    
    return RedirectResponse(url="/documents", status_code=303)

async def process_with_your_ai(file_path: str, filename: str, document_type: str):
    """
    INTEGRATION POINT: Replace this with YOUR actual AI processing
    from Phase 1
    """
    # YOUR existing AI code goes here
    # This should call your document classification, extraction, and summarization
    
    if document_type == "auto":
        # Call your classification model
        doc_type = "invoice"  # Replace with actual classification
    else:
        doc_type = document_type
    
    # Call your extraction models based on document type
    extracted_data = {
        "vendor": "Extracted Vendor Name",
        "amount": 1500.00,
        "due_date": "2024-01-20",
        "invoice_number": "INV-2024-001"
    }
    
    # Call your summarization model
    summary = "AI-generated summary based on extracted information"
    
    return {
        "document_type": doc_type,
        "extracted_data": extracted_data,
        "summary": summary,
        "confidence_score": 0.89,
        "processing_status": "completed"
    }

@app.post("/logout")
async def logout_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in user_sessions:
        del user_sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)