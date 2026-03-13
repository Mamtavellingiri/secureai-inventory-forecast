from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku_code = Column(String(50), unique=True, nullable=False)
    category = Column(String(100))
    name = Column(String(200))
    base_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = relationship("Sales", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product")
    promotions = relationship("Promotion", back_populates="product")

class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    store_id = Column(String(50), unique=True)
    city = Column(String(100))
    region = Column(String(100))
    
    # Relationships
    sales = relationship("Sales", back_populates="location")
    forecasts = relationship("Forecast", back_populates="location")
    promotions = relationship("Promotion", back_populates="location")

class Sales(Base):
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    sku_id = Column(Integer, ForeignKey('products.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
    sales_quantity = Column(Integer, default=0)
    returns_quantity = Column(Integer, default=0)
    out_of_stock_flag = Column(Boolean, default=False)
    price = Column(Float)
    
    # Relationships
    product = relationship("Product", back_populates="sales")
    location = relationship("Location", back_populates="sales")

class Promotion(Base):
    __tablename__ = 'promotions'
    
    id = Column(Integer, primary_key=True)
    sku_id = Column(Integer, ForeignKey('products.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    discount_percentage = Column(Float)
    promotion_type = Column(String(50))
    
    # Relationships
    product = relationship("Product", back_populates="promotions")
    location = relationship("Location", back_populates="promotions")

class Forecast(Base):
    __tablename__ = 'forecasts'
    
    id = Column(Integer, primary_key=True)
    sku_id = Column(Integer, ForeignKey('products.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
    forecast_date = Column(Date)
    predicted_demand = Column(Float)
    reorder_point = Column(Float)
    safety_stock = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="forecasts")
    location = relationship("Location", back_populates="forecasts")