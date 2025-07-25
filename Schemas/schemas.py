from pydantic import BaseModel, Field,EmailStr


class UserCreate(BaseModel):
    name : str = Field(...,max_length=50)
    username : str = Field(...,min_length=3,max_length=20)
    phone : str = Field(...,min_length=10, max_length=10, pattern ="^[0-9]{10}$") 
    email : EmailStr 
    password : str = Field(...,min_length=6)
    role_id : int 

class loggedIn(BaseModel):
    username : str
    password : str

class RoleOut(BaseModel):
    name : str
class ShowUser(BaseModel):
    id : int 
    name : str
    username : str
    phone : str
    email : EmailStr
    role : RoleOut
    class Config :
        orm_mode = True

class ShowUserBasic(BaseModel):
    id : int 
    name : str
    username : str
    phone : str
    email : EmailStr
    role : str