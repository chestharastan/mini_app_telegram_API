from pydantic import BaseModel


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int


class CreateOrderRequest(BaseModel):
    initData: str
    items: list[OrderItem]
    total: float