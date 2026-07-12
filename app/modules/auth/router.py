from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.modules.auth import User
from app.modules.auth.schema import UserRegister, UserResponse, Token
from app.modules.auth.service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter()

# Register API
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """
    Register the Master Administrator account.
    
    This is a personal app, meaning registration is strictly restricted and locked down
    after the first successful registration has occurred.
    """
    # check if any user already exists in the database
    any_user_statement = select(User)
    any_user_result = await session.exec(any_user_statement)
    if any_user_result.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Admin user already exists."
        )

    # checking if username is already taken
    statement = select(User).where(User.username == user_in.username)
    result = await session.exec(statement)
    existing_user = result.first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # hashing the password and creating a new user object
    hashed_pw = hash_password(user_in.password)
    new_user = User(username=user_in.username, hashed_password=hashed_pw)
    
    # saving in database (asynchronously)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

# Token API
@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    OAuth2-compatible token exchange endpoint.
    
    Accepts form data containing username and password, authenticates credentials,
    and returns a stateless JWT token.
    """
    # finding user in database
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.first()
    
    # checking username and password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # creating token for user
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}

# Get User API
@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve currently logged-in administrator profile details.
    
    Requires a valid JWT Bearer token in the Authorization header.
    """
    return current_user
