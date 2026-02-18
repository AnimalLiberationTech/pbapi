from typing import Optional

from src.schemas.common import CountryCode
from src.schemas.osm_data import OsmData
from src.schemas.schema_base import SchemaBase


class Shop(SchemaBase):
    id: Optional[int] = None
    country_code: CountryCode
    company_id: str
    shop_address: str
    osm_data: OsmData
