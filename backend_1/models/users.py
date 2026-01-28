# models/user_mysql.py
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
import mysql.connector
from backend.db.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]


class MySQLDatabase:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                database=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD
                dictionary=True
            )
        except Exception as e:
            print(f"MySQL connection error: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch and query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.fetchall() if cursor.description else []
                
            return result
        except Exception as e:
            self.connection.rollback()
            print(f"MySQL query error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()

class User:
    def __init__(self, db_connection: MySQLDatabase):
        self.db = db_connection

    def create_user(self, user_data: UserCreate) -> UserResponse:
        password_hash = pwd_context.hash(user_data.password)
        user_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO users (id, email, password_hash, first_name, last_name, company)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.db.execute_query(
            query, 
            (user_id, user_data.email, password_hash, user_data.first_name, 
             user_data.last_name, user_data.company),
            fetch=False
        )
        
        # Create default folders for user
        self._create_default_folders(user_id)
        
        # Get created user
        user = self.get_user_by_id(user_id)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
        result = self.db.execute_query(query, (email,))
        
        if not result or not pwd_context.verify(password, result[0]['password_hash']):
            return None
        
        # Update last login
        user_id = result[0]['id']
        update_query = "UPDATE users SET last_login = %s WHERE id = %s"
        self.db.execute_query(update_query, (datetime.now(), user_id), fetch=False)
        
        return UserResponse(**{k: v for k, v in result[0].items() 
                             if k != 'password_hash'})

    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        query = "SELECT * FROM users WHERE id = %s AND is_active = TRUE"
        result = self.db.execute_query(query, (user_id,))
        
        if not result:
            return None
            
        return UserResponse(**{k: v for k, v in result[0].items() 
                             if k != 'password_hash'})


    def _create_default_folders(self, user_id: str):
        """Create default folders for new user using stored procedure"""
        try:
            # Call stored procedure
            cursor = self.db.connection.cursor()
            cursor.callproc('CreateDefaultFolders', [user_id])
            self.db.connection.commit()
            cursor.close()
        except Exception as e:
            # Fallback if stored procedure doesn't exist
            print(f"Stored procedure failed, using fallback: {e}")
            default_folders = ['Emails', 'Forms', 'Resumes', 'Invoices', 'Letters', 'News_articles']
            
            for folder_name in default_folders:
                query = "INSERT INTO document_folders (user_id, name) VALUES (%s, %s)"
                self.db.execute_query(query, (user_id, folder_name), fetch=False)

    def create_session(self, user_id: str) -> str:
        """Create a new user session"""
        session_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)
        
        query = """
        INSERT INTO user_sessions (user_id, session_token, expires_at)
        VALUES (%s, %s, %s)
        """
        self.db.execute_query(query, (user_id, session_token, expires_at), fetch=False)
        
        return session_token

    def validate_session(self, session_token: str) -> Optional[UserResponse]:
        """Validate session token and return user"""
        query = """
        SELECT u.* FROM users u
        JOIN user_sessions us ON u.id = us.user_id
        WHERE us.session_token = %s AND us.expires_at > %s AND u.is_active = TRUE
        """
        
        result = self.db.execute_query(query, (session_token, datetime.now()))
        
        if not result:
            return None
            
        return UserResponse(**{k: v for k, v in result[0].items() 
                             if k != 'password_hash'})