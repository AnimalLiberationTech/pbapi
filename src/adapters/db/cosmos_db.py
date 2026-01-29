import os
from abc import ABC
from typing import Self, Dict, Any

from azure.cosmos import exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.cosmos_client import CosmosClient
from azure.cosmos.database import DatabaseProxy
from azure.cosmos.partition_key import PartitionKey

from src.adapters.db.base import BaseDBAdapter
from src.schemas.common import EnvType, TableName, Operator


class CosmosDBAdapter(BaseDBAdapter, ABC):
    container = None
    db = None

    def __init__(self, env: EnvType, logger):
        super().__init__(env, logger)
        self.client = CosmosClient(
            os.environ[f"{env.upper()}_COSMOS_DB_ACCOUNT_HOST"],
            {"masterKey": os.environ[f"{env.upper()}_COSMOS_DB_ACCOUNT_KEY"]},
        )

    def use_db(self, db_name: str) -> Self:
        self.db: DatabaseProxy = self.client.get_database_client(db_name)
        return self

    def use_table(self, table_name: TableName) -> Self:
        self.container: ContainerProxy = self.db.get_container_client(table_name)
        return self

    def create_one(self, data: Dict[str, Any]) -> str:
        try:
            return self.container.create_item(data)["id"]
        except exceptions.CosmosResourceExistsError:
            return data["id"]

    def create_or_update_one(self, data: Dict[str, Any]) -> str:
        return self.container.upsert_item(data)["id"]

    def read_one(self, _id: str, **kwargs) -> Dict[str, Any] | None:
        try:
            return self.container.read_item(_id, kwargs["partition_key"])
        except KeyError as exc:
            raise KeyError("missing argument: 'partition_key'") from exc
        except exceptions.CosmosResourceNotFoundError:
            return None

    def read_many(
        self, where: dict[str, str | tuple] | None = None, limit=10, **kwargs
    ) -> list[dict[str, Any]]:
        partition_key = kwargs.get("partition_key")
        if partition_key is None:
            raise ValueError("partition_key is required")
        if where:
            where_str, where_params = format_where(where)
            return list(
                self.container.query_items(
                    f"SELECT * FROM r WHERE {where_str}",
                    where_params,
                    partition_key,
                    max_item_count=limit,
                )
            )
        return list(self.container.read_all_items(limit))

    def update_one(self, _id: str, data: Dict[str, Any]) -> bool:
        response = self.container.replace_item(_id, data)
        return bool(response["_ts"])

    def delete_one(self, _id: str, **kwargs) -> bool:
        partition_key = kwargs.get("partition_key")
        if partition_key is None:
            raise ValueError("partition_key is required")

        self.container.delete_item(_id, partition_key)
        return True

    def create_db(self, db_id: str | None = None) -> Self:
        if not db_id:
            db_id = os.environ[f"{self.env.upper()}_COSMOS_DB_DATABASE_ID"]
        try:
            self.db: DatabaseProxy = self.client.create_database(db_id)
            self.logger.info("Database with id '%s' created", db_id)
        except exceptions.CosmosResourceExistsError:
            self.logger.info("Database with id '%s' already exists", db_id)
            self.db = self.client.get_database_client(db_id)
        return self

    def create_table(self, table_name: TableName, **kwargs) -> Self:
        partition_key = kwargs.get("partition_key")
        if partition_key is None:
            raise ValueError("partition_key is required")

        try:
            self.container = self.db.create_container(
                table_name, PartitionKey(path=f"/{partition_key}")
            )
            self.logger.info("Container with id '%s' created", table_name)
        except exceptions.CosmosResourceExistsError:
            self.logger.info("Container with id '%s' already exists", table_name)
            self.container = self.db.get_container_client(table_name)
        return self

    def drop_table(self, table_name: TableName) -> None:
        try:
            self.db.delete_container(table_name)
        except exceptions.CosmosResourceNotFoundError:
            pass

    def drop_db(self) -> None:
        try:
            self.client.delete_database(self.db)
            self.logger.info("Database with id '%s' dropped", self.db.id)
        except exceptions.CosmosResourceNotFoundError:
            self.logger.info("Database with id '%s' was not found", self.db.id)


# Function to format the where clause for CosmosDB query
def format_where(where: dict[str, str | tuple]) -> tuple[str, list[dict[str, Any]]]:
    where_str = ""
    where_params = []
    for key, value in where.items():
        if isinstance(value, tuple):
            if value[0] == Operator.NE:
                where_str += f"r.{key}!=@{key} AND "
                where_params.append({"name": f"@{key}", "value": value[1]})
        else:
            where_str += f"r.{key}=@{key} AND "
            where_params.append({"name": f"@{key}", "value": value})

    return where_str.rstrip(" AND "), where_params


def init_db_session(logger) -> CosmosDBCoreAdapter:
    env_name = os.environ["ENV_NAME"]
    db_name = os.environ[f"{env_name.upper()}_COSMOS_DB_DATABASE_ID"]
    return CosmosDBCoreAdapter(EnvType(env_name), logger).use_db(db_name)
