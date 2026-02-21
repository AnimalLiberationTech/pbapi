from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from src.helpers.common import osm_type_to_code
from src.schemas.common import CountryCode
from src.schemas.osm_data import OsmData
from src.schemas.schema_base import SchemaBase


class Shop(SchemaBase):
    id: Optional[int] = None
    osm_id: str | None = None
    country_code: CountryCode
    company_id: str
    address: str
    osm_data: OsmData
    creator_user_id: UUID
    creation_time: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

    # for Plante schema backward compatibility
    def model_post_init(self, __context) -> None:
        self.osm_id = f"{osm_type_to_code(self.osm_data.type)}:{self.osm_data.key}"
