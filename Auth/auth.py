from fastapi import FastAPI,HTTPException,Depends,status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from typing import Optional,Annotated,List
from Database.database import SessionLocal,engine
from sqlalchemy.orm import Session
from datetime import datetime,timedelta, timezone
from jose import JWTError,jwt
from passlib.context import CryptContext
from Models import models
from Schemas import schemas,hotelschemas,bookings,token


def getdb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(getdb)]

mod = models
sch = schemas
hotel = hotelschemas
book = bookings.ShowBookings
booknow = bookings.BookHotel


SECRET_KEY = "b55fa629a5f4642d8810cf547a0caca7152919e352be6f8ef73b807b2d626f4c" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token : Annotated[str,Depends(oauth2_scheme)],db : db_dependency):
    credential_exceptions = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Could not validate user",
        headers= {"WWW-Authenticate" : "Bearer"},
        )
    try :
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise credential_exceptions
    except JWTError:
        raise credential_exceptions
    user = db.query(mod.User).filter(mod.User.username == username).first()
    if user is None :
        raise credential_exceptions
    print("Authenticated", username)
    return user


def get_current_admin(token : Annotated[str,Depends(oauth2_scheme)],db : db_dependency):
    credential_exceptions = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Could not validate user",
        headers= {"WWW-Authenticate" : "Bearer"},
        )
    try :
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credential_exceptions
    except JWTError:
        raise credential_exceptions
    user = db.query(mod.User).filter(mod.User.username == username).first()
    if user is None or role != "admin":
        raise credential_exceptions
    return user
