from pydantic import BaseModel, Field

# DTO for user registration
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]*$")
    password: str = Field(..., min_length=8, pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

# DTO for user response after successful registration
class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        # enable ORM mode
        from_attributes = True

# DTO for token response
class Token(BaseModel):
    access_token: str
    token_type: str

# DTO for token data
class TokenData(BaseModel):
    username: str | None = None
