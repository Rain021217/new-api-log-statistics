from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(default="")
    password: str = Field(default="")

