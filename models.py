from typing import List, Optional, Union
from sqlalchemy import String, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Products(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(primary_key=True)
    name = Mapped[Optional[str]]
    price = Mapped[Union[int, float]]

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] 
    warehouse_id: Mapped[int]
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"))
    quantity: Mapped[int]

def create_tables():
    engine = create_engine("sqlite:///inventory.db")
    Products.metadata.create_all(engine)
    Inventory.metadata.create_all(engine)


create_tables()