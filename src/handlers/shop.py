from src.adapters.db.postgresql import init_db_session, PostgreSQLAdapter
from src.schemas.common import TableName
from src.schemas.shop import Shop


class ShopHandler:
    def __init__(self, logger):
        self.logger = logger
        self.db: PostgreSQLAdapter = init_db_session(self.logger)

    def get_or_create(self, shop: Shop) -> Shop:
        self.db.use_table(TableName.SHOP)
        shops = self.db.read_many({"osm_id": shop.osm_id}, limit=1)
        self.logger.info(shops)
        if shops:
            # for Plante schema backward compatibility
            if shops[0]["country_code"] is None:
                shops[0]["country_code"] = shop.country_code
            if shops[0]["company_id"] is None:
                shops[0]["company_id"] = shop.company_id
            if shops[0]["address"] is None:
                shops[0]["address"] = shop.address
            if shops[0]["osm_data"] is None:
                shops[0]["osm_data"] = shop.osm_data

            return Shop(**shops[0])

        shop_id = self.db.create_one(shop.model_dump(mode="json"))
        self.logger.info(shop_id)
        shop.id = int(shop_id)
        return shop
