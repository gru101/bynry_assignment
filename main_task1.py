from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Products, Inventory  

app = FastAPI(debug=True)

engine = create_engine("sqlite:///inventory.db", echo=True)

# Pydantic model for validation
class Product(BaseModel):
    name: Optional[str]
    sku: str
    price: int
    warehouse_id: int
    quantity: int

@app.post("/api/products")
def save_product(product: Product):
    data = product.model_dump()

    try:
        with Session(engine) as session:
            # Create new product
            new_product = Products(
                name=data['name'],
                sku=data['sku'],
                price=data['price'],
                warehouse_id=data['warehouse_id']
            )
            session.add(new_product)
            session.flush()  # ensures new_product.id is available

            # Create inventory entry
            new_inventory = Inventory(
                product_id=new_product.id,
                warehouse_id=data['warehouse_id'],
                quantity=data['quantity']
            )
            session.add(new_inventory)

            # Commit transaction (both inserts at once)
            session.commit()

            return {
                "message": "Product created successfully",
                "product_id": new_product.id
            }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create product"
        }