from http import HTTPStatus

from src.adapters.db.postgresql import init_db_session
from src.helpers.osm import validate_osm_url, parse_osm_url, lookup_osm_data
from src.schemas.common import TableName, OsmType
from src.schemas.osm_data import OsmData
from src.schemas.shop import Shop


def link_shop_handler(
    url: str, user_id: str, receipt_id: str, logger
) -> (HTTPStatus, dict):
    if not validate_osm_url(url):
        return HTTPStatus.BAD_REQUEST, {"msg": "Unsupported URL"}

    session = init_db_session(logger)
    session.use_table(TableName.RECEIPT)
    receipt = session.read_one(receipt_id, partition_key=user_id)
    if not receipt:
        return HTTPStatus.NOT_FOUND, {"msg": "Receipt not found"}

    # double check that the shop doesn't exist
    session.use_table(TableName.SHOP)
    shops = session.read_many(
        {"company_id": receipt["company_id"], "shop_address": receipt["shop_address"]},
        partition_key=receipt["country_code"],
        limit=1,
    )
    if shops:
        shop = shops[0]
    else:
        try:
            osm_type, osm_key = parse_osm_url(url)
        except ValueError:
            return HTTPStatus.BAD_REQUEST, {"msg": "Invalid OSM URL"}

        osm_shop_data = lookup_osm_data(osm_type, osm_key)
        if not osm_shop_data:
            return HTTPStatus.BAD_REQUEST, {"msg": "Failed to get OSM shop details"}

        osm_data = OsmData(
            type=OsmType(osm_type),
            key=int(osm_key),
            lat=osm_shop_data["lat"],
            lon=osm_shop_data["lon"],
            display_name=osm_shop_data["display_name"],
            address=osm_shop_data["address"],
        )
        shop = Shop(
            country_code=receipt["country_code"],
            company_id=receipt["company_id"],
            shop_address=receipt["shop_address"],
            osm_data=osm_data,
        ).model_dump(mode="json")
        session.use_table(TableName.SHOP)
        session.create_one(shop)

    session.use_table(TableName.RECEIPT)
    receipt["shop_id"] = shop["id"]
    session.update_one(receipt_id, receipt)
    return HTTPStatus.OK, {
        "msg": "Shop successfully linked",
        "data": {"shop_id": shop["id"]},
    }
