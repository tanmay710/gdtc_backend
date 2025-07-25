from pydantic import BaseModel, Field,EmailStr
from Schemas import schemas,hotelschemas
from datetime import date
class ShowBookings(BaseModel):

    id : int
    user : schemas.ShowUser
    hotel : hotelschemas.HotelSchemas
    check_in : date
    check_out : date

    class Config:
        orm_mode = True

class BookHotel(BaseModel):
    hotel_id : int
  
    check_in : date
    check_out : date

    class Config:
        orm_mode = True