from sqlalchemy import Column,Integer,String,Boolean,ForeignKey,Date
from sqlalchemy.orm import relationship
from Database.database import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer,primary_key=True,index = True)
    name = Column(String(20),unique = True,nullable = False)

    user = relationship("User",back_populates= "role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True, index=True)

    name = Column(String(50))
    email = Column(String(50))
    phone= Column(String(10), unique= True )
    username = Column(String(50),unique=True)
    password = Column(String(255))

    role_id = Column(Integer,ForeignKey("roles.id"))

    role = relationship("Role",back_populates= "user")
    booking = relationship("Bookings", back_populates= "user")


class Hotels(Base):
    __tablename__ = "hotels"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(50),nullable = False)
    location = Column(String(50),nullable=False) 
    price = Column(Integer,nullable= False)
    image_url= Column(String(255),nullable=True)
    booking = relationship("Bookings",back_populates= "hotel")



class Bookings(Base):
    __tablename__ = "bookings"
    id = Column(Integer,primary_key= True,index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    hotel_id = Column(Integer,ForeignKey("hotels.id"))
    check_in = Column(Date ,nullable = False)
    check_out = Column(Date,nullable = False)
    

    user = relationship("User",back_populates= "booking")
    hotel = relationship("Hotels",back_populates= "booking")

    

