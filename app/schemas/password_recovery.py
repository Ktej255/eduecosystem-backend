from pydantic import BaseModel, EmailStr


class PasswordRecovery(BaseModel):
    email: str
