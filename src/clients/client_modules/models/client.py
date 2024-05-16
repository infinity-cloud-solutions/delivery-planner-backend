from pydantic import BaseModel
from pydantic import StrictStr, StrictFloat


class HIBerryClient(BaseModel):
    phone_number: str
    name: StrictStr
    address: str
    email: StrictStr | None = None


class Geolocation(BaseModel):
    latitude: StrictFloat
    longitude: StrictFloat
