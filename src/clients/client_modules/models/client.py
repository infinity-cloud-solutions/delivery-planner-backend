from pydantic import BaseModel
from pydantic import StrictStr, StrictFloat, StrictBool


class Geolocation(BaseModel):
    latitude: StrictFloat | None = None
    longitude: StrictFloat | None = None


class HIBerryBaseClient(BaseModel):
    phone_number: StrictStr
    original_phone_number: StrictStr | None = None
    name: StrictStr
    address: str
    discount: StrictStr | None = None
    second_address: str | None = None
    address_geolocation: Geolocation | None = None
    second_address_geolocation: Geolocation | None = None
    email: StrictStr | None = None
    delete_old_record: StrictBool | None = None


class HIBerryClient(HIBerryBaseClient):
    pass


class HIBerryClientUpdate(HIBerryBaseClient):
    pass
