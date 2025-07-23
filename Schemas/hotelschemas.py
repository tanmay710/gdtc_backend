from pydantic import BaseModel, Field,EmailStr
class HotelSchemas(BaseModel):
    id : int
    name : str
    location : str
    price : int
    image_url : str
    class Config:
        orm_mode = True