# routes/auth_mysql.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from models.users import UserCreate, UserLogin,MySQLDatabase
from auth.auth_services import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_db():
    db = MySQLDatabase()
    db.connect()
    try:
        yield db
    finally:
        db.close()

def get_auth_service(db=Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_session_token(authorization: str = Header(...)) -> str:
    """Extract session token from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    return authorization[7:]

@router.post("/register")
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account"""
    return auth_service.register_user(user_data)

@router.post("/login")
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user"""
    return auth_service.login_user(login_data)

@router.post("/logout")
async def logout_user(
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user"""
    auth_service.logout_user(session_token)
    return {"message": "Logout successful"}

@router.get("/me")
async def get_current_user(
    session_token: str = Depends(get_session_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user information"""
    return auth_service.get_current_user(session_token)


# @router.post("/change-password")
# async def change_password(
#     current_password: str,
#     new_password: str,
#     session_token: str = Depends(get_session_token),
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """Change user password"""
#     user = auth_service.get_current_user(session_token)
#     auth_service.change_password(user.id, current_password, new_password)
#     return {"message": "Password changed successfully"}