from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "eduecosystem-super-secret-key-2025"
ALGORITHM = "HS256"

def create_reset_token(email):
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"exp": expire, "sub": str(email)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

if __name__ == "__main__":
    token = create_reset_token("chitrakumawat33@gmail.com")
    print(f"TOKEN: {token}")
    with open("token.txt", "w") as f:
        f.write(token)
    with open("token.txt", "w") as f:
        f.write(token)
