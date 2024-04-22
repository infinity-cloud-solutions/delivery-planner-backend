from pydantic import BaseModel
from pydantic import StrictStr
from pydantic import confloat


class HIBerryProduct(BaseModel):
    name: StrictStr
    price: confloat(ge=0.0)


class HIBerryProductUpdate(HIBerryProduct):
    id: StrictStr
