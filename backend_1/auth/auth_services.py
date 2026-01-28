# services/auth_service_mysql.py
from fastapi import HTTPException, status
from models.users import User, UserCreate, UserLogin, UserResponse, MySQLDatabase
from db.config import settings

class AuthService:
    def __init__(self, db_connection: MySQLDatabase):
        self.db = db_connection
        self.user_model = User(db_connection)

    def register_user(self, user_data: UserCreate) -> dict:
        """Register a new user"""
        # Check if user already exists
        check_query = "SELECT id FROM users WHERE email = %s"
        existing_user = self.db.execute_query(check_query, (user_data.email,))
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        user = self.user_model.create_user(user_data)
        
        # Create session
        session_token = self.user_model.create_session(user.id)
        
        return {
            "user": user,
            "session_token": session_token,
            "message": "User registered successfully"
        }

    def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate and login user"""
        user = self.user_model.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create new session
        session_token = self.user_model.create_session(user.id)
        
        return {
            "user": user,
            "session_token": session_token,
            "message": "Login successful"
        }

    def logout_user(self, session_token: str):
        """Logout user by invalidating session"""
        query = "DELETE FROM user_sessions WHERE session_token = %s"
        self.db.execute_query(query, (session_token,), fetch=False)

    def get_current_user(self, session_token: str) -> UserResponse:
        """Get current user from session token"""
        user = self.user_model.validate_session(session_token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        return user

    # def change_password(self, user_id: str, current_password: str, new_password: str):
    #     """Change user password"""
    #     # Verify current password
    #     query = "SELECT password_hash FROM users WHERE id = %s"
    #     result = self.db.execute_query(query, (user_id,))
        
    #     if not result or not pwd_context.verify(current_password, result[0]['password_hash']):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Current password is incorrect"
    #         )
        
    #     # Update password
    #     new_password_hash = pwd_context.hash(new_password)
    #     update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
    #     self.db.execute_query(update_query, (new_password_hash, user_id), fetch=False)