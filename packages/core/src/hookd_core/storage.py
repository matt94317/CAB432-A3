"""Build the stores from settings: DynamoDB (A3) or in-memory (tests, quick local runs)."""

from dataclasses import dataclass
from typing import Literal

from hookd_core.repositories.assignments import InMemoryAssignmentRepository
from hookd_core.repositories.campaigns import InMemoryCampaignRepository
from hookd_core.repositories.creators import InMemoryCreatorRepository
from hookd_core.repositories.posts import InMemoryPostRepository
from hookd_core.repositories.users import InMemoryUserRepository, UserRepository
from hookd_core.sync import Stores

StorageKind = Literal["dynamodb", "memory"]


@dataclass(frozen=True)
class Storage:
    stores: Stores
    users: UserRepository


def make_storage(
    kind: StorageKind,
    *,
    table_name: str = "",
    region: str = "ap-southeast-2",
    endpoint_url: str | None = None,
    create_table: bool = False,
) -> Storage:
    if kind == "memory":
        # Per process: the API and worker don't share data, so use SYNC_MODE=inline
        return Storage(
            stores=Stores(
                campaigns=InMemoryCampaignRepository(),
                creators=InMemoryCreatorRepository(),
                assignments=InMemoryAssignmentRepository(),
                posts=InMemoryPostRepository(),
            ),
            users=InMemoryUserRepository(),
        )

    import boto3

    from hookd_core.repositories import dynamodb as ddb

    if not table_name:
        raise ValueError("STORAGE=dynamodb needs DYNAMODB_TABLE")
    resource = boto3.resource("dynamodb", region_name=region, endpoint_url=endpoint_url)
    table = ddb.create_table(resource, table_name) if create_table else resource.Table(table_name)
    return Storage(
        stores=Stores(
            campaigns=ddb.DynamoCampaignRepository(table),
            creators=ddb.DynamoCreatorRepository(table),
            assignments=ddb.DynamoAssignmentRepository(table),
            posts=ddb.DynamoPostRepository(table),
        ),
        users=ddb.DynamoUserRepository(table),
    )
