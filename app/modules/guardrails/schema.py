from pydantic import BaseModel, Field

class SecurityCheckRequest(BaseModel):
    """Input payload to check a proposed bash command for security threats."""
    command: str = Field(..., min_length=1)

class SecurityCheckResponse(BaseModel):
    """Result of the semantic safety check against the dangerous commands database."""
    safe: bool
    reason: str
    similarity: float

class BlacklistPatternCreate(BaseModel):
    """Payload to register a new forbidden pattern inside the semantic guardrail database."""
    pattern: str = Field(..., min_length=3)
    reason: str = Field(..., min_length=3)

class BlacklistPatternResponse(BaseModel):
    """Details of a registered dangerous command pattern in the vector store."""
    id: str
    pattern: str
    reason: str
