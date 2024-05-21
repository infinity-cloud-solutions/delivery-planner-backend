from pydantic import BaseModel
from pydantic import StrictStr, StrictFloat

class Geolocation(BaseModel):
    latitude: StrictFloat
    longitude: StrictFloat


class HIBerryBaseClient(BaseModel):
    phone_number: StrictStr
    name: StrictStr
    address: str
    discount: StrictStr | None = None
    second_address: str | None = None
    address_geolocation: Geolocation | None = None
    second_address_geolocation: Geolocation | None = None
    email: StrictStr | None = None


class HIBerryClient(HIBerryBaseClient):
    pass


class HIBerryClientUpdate(HIBerryBaseClient):
    pass