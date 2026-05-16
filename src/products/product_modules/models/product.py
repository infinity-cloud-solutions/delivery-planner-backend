from pydantic import BaseModel, StrictStr, confloat


class HIBerryProduct(BaseModel):
    name: StrictStr
    price: confloat(ge=0.0)


class HIBerryProductUpdate(HIBerryProduct):
    id: StrictStr
