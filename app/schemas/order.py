from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class OrderItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(validation_alias=AliasChoices("product_id", "productId", "id"))
    quantity: int = Field(gt=0, validation_alias=AliasChoices("quantity", "qty"))


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    initData: str = Field(validation_alias=AliasChoices("initData", "init_data"))
    customerPhone: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("customerPhone", "customer_phone"),
    )
    items: list[OrderItem]
