from src.adapters.db.postgresql import init_db_session, PostgreSQLAdapter
from src.schemas.common import TableName
from src.schemas.shop import Shop


class ShopHandler:
    def __init__(self, logger):
        self.logger = logger
        self.db: PostgreSQLAdapter = init_db_session(self.logger)

    def get_or_create(self, shop: Shop) -> Shop:
        self.db.use_table(TableName.SHOP)
        shops = self.db.read_many(
            {
                "country_code": shop.country_code,
                "company_id": shop.company_id,
                "shop_address": shop.shop_address,
            },
            limit=1,
        )
        if shops:
            return Shop(**shops[0])

        shop_id = self.db.create_one(shop.model_dump(mode="json"))
        shop.id = int(shop_id)
        return shop
