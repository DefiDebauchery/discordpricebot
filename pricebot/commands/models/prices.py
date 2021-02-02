from sqlalchemy import *  # func, Table, Column, Boolean, BigInteger, Binary, DateTime, Integer, Float, String
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PriceATH(Base):
    __tablename__ = 'price_ath'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now(), server_onupdate=func.now())

    def __repr__(self):
        return f"<ATH of {self.price} for {str(self.token)} at {self.timestamp}>"
