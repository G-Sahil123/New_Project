from fastapi import FastAPI, Request ,UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr ,field_validator
import uvicorn
import mysql.connector
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from src.DocumindAI.ml_pipeline.prediction import PredictionPipeline
from pathlib import Path
import shutil
from uuid import uuid4
from passlib.context import CryptContext

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

dotenv_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
load_dotenv(dotenv_path)

app = FastAPI(title ="DocumindAI",version="1.0")

# Jinja2 template loader
templates = Jinja2Templates(directory="frontend/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

def get_current_user(request: Request)->int:
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return int(user_id)

class RegisterUser(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def strong_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$", v):
            raise ValueError("Weak password")
        return v    

# Serve UI at root "/"
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    user = RegisterUser(
        full_name=full_name,
        email=email,
        password=password)
    hashed_pw = pwd_context.hash(user.password)
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(400, "Email already exists")

    cur.execute("""
        INSERT INTO users
        (full_name,email,password)
        VALUES (%s,%s,%s)
    """, (user.full_name, user.email, hashed_pw))
    conn.commit()
    conn.close()

    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT user_id,password FROM users WHERE email=%s",
        (email,)
    )
    user = cur.fetchone()
    conn.close()

    if not user or not pwd_context.verify(password,user["password"]):
        raise HTTPException(401, "Invalid credentials")

    response = RedirectResponse("/predict", status_code=302)
    response.set_cookie("user_id", str(user["user_id"]), httponly=True)
    return response

# Training route
@app.get("/train-ui", response_class=HTMLResponse)
async def train(request: Request,user_id: int = Depends(get_current_user)):
    return templates.TemplateResponse("train.html", {"request": request})

@app.post("/train")
async def training(user_id: int = Depends(get_current_user)):
    try:
        os.system("python main.py")
        # os.system("dvc repro")
        return {"message": "Training successful !!"}
    except Exception as e:
        raise HTTPException(500, str(e))

# Prediction route
@app.get("/predict", response_class=HTMLResponse)
async def predict_form(request: Request,user_id: int = Depends(get_current_user)):
    return templates.TemplateResponse("predict.html", {"request": request})

@app.post("/predict")
async def predict(file:UploadFile=File(...),user_id: int=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
          
    if file.content_type not in {"image/tiff", "image/jpeg", "image/png","image/tif","image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
        
    suffix = Path(file.filename).suffix
    safe_name = f"{uuid4().hex}{suffix}"  
    file_path = UPLOAD_DIR/safe_name

    with open(file_path,"wb") as f:
        shutil.copyfileobj(file.file,f)

    try:
        pipeline = PredictionPipeline(file_path)
        prediction, metadata = pipeline.predict()
        return {"document_type": prediction}
    except Exception:
            raise HTTPException(500, "Prediction failed")
    finally:
        if file_path.exists():
            file_path.unlink()
    
@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("user_id")
    return response    


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)