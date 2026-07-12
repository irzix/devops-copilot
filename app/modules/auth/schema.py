from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    """
    DTO payload containing registration credentials for the single administrator.
    Enforces pattern restrictions on both username and password for security.
    """
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]*$")
    password: str = Field(..., min_length=8, pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

class UserResponse(BaseModel):
    """
    Safe database projection of user information (excludes hashed password details).
    """
    id: int
    username: str
    is_active: bool

    class Config:
        # Enable ORM attribute resolution mapping
        from_attributes = True

class Token(BaseModel):
    """
    Authentication token response payload containing the JWT string.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Parsed JWT token container payload containing the username claim.
    """
    username: str | None = None
