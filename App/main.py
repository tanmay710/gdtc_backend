from fastapi import FastAPI,HTTPException,Depends,status,Query,UploadFile,File,Form,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field,EmailStr
from typing import Optional,Annotated,List
from Models import models
from Database.database import SessionLocal,engine
from Schemas import schemas,hotelschemas,bookings,token
from sqlalchemy.orm import Session
from datetime import datetime,timedelta, timezone
from jose import JWTError,jwt
from passlib.context import CryptContext
from sqlalchemy import asc,desc, func
from Auth.auth import get_password_hash,verify_password,ACCESS_TOKEN_EXPIRE_MINUTES,create_access_token,get_current_user,get_current_admin
import os
import shutil
from uuid import uuid4

UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR,exist_ok=True)


    

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




api = FastAPI()
mod.Base.metadata.create_all(bind = engine)

api.mount("/static",StaticFiles(directory= "App/static"),name="static")

api.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:4200"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)



@api.post("/register",status_code= status.HTTP_201_CREATED,response_model= sch.ShowUser)
async def register_user(db : db_dependency,user : sch.UserCreate):
    user_exists = db.query(mod.User).filter((mod.User.username == user.username) | (mod.User.email == user.email) | 
                                            (mod.User.phone == user.phone)).first()
    if user_exists != None:
        raise HTTPException(status_code=404,detail = "User already exists")
    hashed_password = get_password_hash(user.password)
    new_user = mod.User(
        name = user.name,
        email = user.email,
        phone = user.phone,
        username = user.username,
        password = hashed_password,
        role_id = user.role_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@api.post("/login", response_model= token.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):

    user = db.query(mod.User).filter(mod.User.username == form_data.username).first()
 
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
 
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role" : user.role.name},  
        expires_delta=access_token_expires
    )
    print(user.role.name)
    return {"access_token": access_token, "token_type": "bearer", "role" : user.role.name, "username": user.username}


@api.get("/hotels", status_code=status.HTTP_200_OK, response_model= List[hotel.HotelSchemas])
async def view_hotel(db : db_dependency, sort_by : Optional[str] = None, order : Optional[str] =None):
    hotels_sorting = db.query(mod.Hotels)
    if sort_by and order :
        attr = getattr(mod.Hotels,sort_by)
        if attr is None:
            raise HTTPException(status_code= 404, detail= "invalid sorting")
        if order.lower() == "asc":
            hotels_sorting = db.query(mod.Hotels).order_by(asc(sort_by))
        elif order.lower() == "desc":
            hotels_sorting = db.query(mod.Hotels).order_by(desc(sort_by))
    hotels = hotels_sorting.all()
    return hotels    

@api.post("/add-hotels", status_code=201)
def add_hotel(
    request : Request,
    name: Annotated[str, Form()],
    location: Annotated[str, Form()],
    price: Annotated[int, Form()],
    image: Annotated[UploadFile, File()],
    db: db_dependency,
    current_user = Depends(get_current_admin)
):

    print("Authorization header: ", request.headers.get("authorization"))
    image_filename = f"{name.replace(' ', '')}{image.filename}"
    image_path = os.path.join("App", "static", image_filename)

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/static/{image_filename}"


    new_hotel = models.Hotels(
        name=name,
        location=location,
        price=price,
        image_url=image_url
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return {"message": "Hotel added successfully", "hotel": {
        "id": new_hotel.id,
        "name": name,
        "image_url": image_url
    }}




@api.get("/users", response_model= sch.ShowUser)
async def get_my_profile(current_user = Depends(get_current_user)):
    return current_user


@api.post("/book", status_code= status.HTTP_201_CREATED)
async def book_hotel(
    booking : booknow,
    db : db_dependency,
    current_user : Annotated[mod.User, Depends(get_current_user)]
):
    print("connected to db", str(engine.url))
    hotel = db.query(mod.Hotels).filter(mod.Hotels.id == booking.hotel_id).first()
    if hotel is None: 
        raise HTTPException(status_code=404,detail="Hotels do not exist")
  

    conflict = db.query(mod.Bookings).filter(mod.Bookings.hotel_id == booking.hotel_id,
                                                mod.Bookings.check_in < booking.check_out,
                                                mod.Bookings.check_out > booking.check_in).first()
    if conflict:
        raise HTTPException(status_code=400, detail = 'hotel already booked on {current date}')
    

    new_booking = mod.Bookings(
        user_id = current_user.id,
        hotel_id = booking.hotel_id,
        check_in = booking.check_in,
        check_out = booking.check_out
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
       
    return {
        "message" : "Booking successfully done",
        "User ID" : current_user.id,
        "User Name" : current_user.name,
        "Hotel Name" : hotel.name,
        "Hotel ID" : booking.hotel_id
    }
 
@api.get("/user-booking", status_code=status.HTTP_202_ACCEPTED, response_model=List[book])
async def ShowUserBooking(
    db: db_dependency,
    current_user: mod.User = Depends(get_current_user)
):
    user_booking = db.query(mod.Bookings).filter(mod.Bookings.user_id == current_user.id).all()
    return user_booking

@api.get("/recent-booking", status_code=status.HTTP_202_ACCEPTED, response_model= book)
async def UserRecentBooking(
    db: db_dependency,
    current_user: mod.User = Depends(get_current_user)
):
    user_booking = db.query(mod.Bookings).filter(mod.Bookings.user_id == current_user.id).order_by(mod.Bookings.id.desc()).first()
    return user_booking
 
 


@api.put("/update", status_code=status.HTTP_202_ACCEPTED, response_model=book)
async def update_booking(
    booking_id: int,
    update: booknow,
    db: db_dependency,
    current_user: mod.User = Depends(get_current_user),
):
    existing_booking = db.query(mod.Bookings).filter(
        mod.Bookings.id == booking_id,
        mod.Bookings.user_id == current_user.id
    ).first()
    
    if existing_booking is None:
        raise HTTPException(status_code=404, detail="No such booking")
 
    hotel = db.query(mod.Hotels).filter(mod.Hotels.id == update.hotel_id).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel does not exist")
 
    db.query(mod.Bookings).filter(
        mod.Bookings.user_id == current_user.id,
        mod.Bookings.hotel_id == existing_booking.hotel_id,
        mod.Bookings.check_in == existing_booking.check_in,
        mod.Bookings.check_out == existing_booking.check_out
    ).delete()
 
    conflict = db.query(mod.Bookings).filter(
        mod.Bookings.hotel_id == update.hotel_id,
        mod.Bookings.check_in < update.check_out,
        mod.Bookings.check_out > update.check_in
    ).first()
 
    if conflict:
        raise HTTPException(status_code=409, detail="Hotel already booked on these dates")
 
    new_booking = mod.Bookings(
        user_id=current_user.id,
        hotel_id=update.hotel_id,
        check_in=update.check_in,
        check_out=update.check_out
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
 
    return {
        "message": "Booking successfully updated",
        "hotel_id": update.hotel_id,
        "check_in": update.check_in,
        "check_out": update.check_out
    }

@api.delete("/cancel", status_code= status.HTTP_202_ACCEPTED)
async def CancelBooking(
    booking_id : int,
    db : db_dependency,
    current_user : mod.User= Depends(get_current_user)
):
    deleted = db.query(mod.Bookings).filter(mod.Bookings.id == booking_id, 
                                            mod.Bookings.user_id == current_user.id).delete()# type: ignore
    if deleted == 0: 
        raise HTTPException(status_code=404,detail= "No such booking")
    
    db.commit()

    return { "message" : "You have successfully cancelled the booking"}




@api.get("/admin/bookings", status_code= status.HTTP_200_OK,response_model=List[book])
async def All_Bookings(
    db : db_dependency,
    admin : Annotated[dict,Depends(get_current_admin)]
):
    
    
    all_bookings = db.query(mod.Bookings).all()
    return all_bookings

@api.get("/admin/users", status_code= status.HTTP_200_OK, response_model= List[sch.ShowUserBasic])
async def All_Users(
    db : db_dependency,
    admin : Annotated[dict,Depends(get_current_admin)]
):
    all_users = db.query(mod.User).filter(mod.User.role.has(name='user'))
    user_list = []
    for user in all_users:
        user_list.append({
            "id" : user.id,
            "name" : user.name,
            "email": user.email,
            "phone" : user.phone,
            "username" : user.username,
            "role" : user.role.name
        })
    return user_list

@api.get("/admin/admins", status_code= status.HTTP_200_OK, response_model= List[sch.ShowUserBasic])
async def All_Admins(
    db : db_dependency,
    admin : Annotated[dict,Depends(get_current_admin)]
):
    all_users = db.query(mod.User).filter(mod.User.role.has(name='admin'))
    admin_list = []
    for user in all_users:
        admin_list.append({
            "id" : user.id,
            "name" : user.name,
            "email": user.email,
            "phone" : user.phone,
            "username" : user.username,
            "role" : user.role.name
        })
    return admin_list

@api.get('/get-dates/{hotel_id}')
def get_dates(hotel_id: int, db: db_dependency):
    bookings = db.query(mod.Bookings).filter(mod.Bookings.hotel_id == hotel_id).all()
    booked_dates = []
    
    for booking in bookings:
        if booking.check_in and booking.check_out: # type: ignore
            current_date = booking.check_in
            while current_date <= booking.check_out: # type: ignore
                booked_dates.append(str(current_date))
                current_date += timedelta(days=1)
 
    return booked_dates


@api.get('/count-bookings')
def most_booked(db : db_dependency, 
                admin : Annotated[dict,Depends(get_current_admin)]):
    today = datetime.today().date()
    last_1_month = today - timedelta(days=30)
    last_6_month = today - timedelta(days= 180)

    def get_data(from_date = None):
        query = db.query(mod.Hotels.name,func.count(mod.Bookings.id).label("count")).join(mod.Bookings).group_by(mod.Hotels.id)
        if from_date:
            query = query.filter(mod.Bookings.check_in >= from_date)

        booking_count = query.all()

        total_bookings = sum(count for _,count in booking_count if count is not None)
        hotels =  [{"Hotel": name, "count": count} for name, count in query.all()]
        return {
            "total_bookings" :total_bookings,
            "hotels" : hotels
        }
    return {
        "last_1_month" : get_data(last_1_month),
        "last_6_month" : get_data(last_6_month),
        "all_time"  : get_data()
    }

@api.get('/revenue')
def revenue_generated(db: db_dependency, admin: Annotated[dict, Depends(get_current_admin)]):
    today = datetime.today().date()
    last_1_month = today - timedelta(days=30)
    last_6_months = today - timedelta(days=180)
 
   
 
    def get_revenue(from_date=None):
        query = db.query(
            mod.Hotels.name,
            func.count(mod.Bookings.id).label("booking_count"),
                (func.count(mod.Bookings.id) * mod.Hotels.price).label("revenue")
            ).join(mod.Bookings).group_by(mod.Hotels.id, mod.Hotels.price)
 
        if from_date:
            
            query = query.filter(mod.Bookings.check_in >= from_date)
 
        hotel_data = query.all()
    
        
 
        total_revenue = sum(row.revenue for row in hotel_data if row.revenue is not None)
        hotels = [{"Hotels": name, "revenue": revenue or 0} for name, _, revenue in hotel_data]
 
        return {
            "total_revenue": total_revenue,
            "hotels": hotels
        }
    return {
         "last_1_month" : get_revenue(last_1_month),
         "last_6_months": get_revenue(last_6_months),
         "all_time" : get_revenue()
    }