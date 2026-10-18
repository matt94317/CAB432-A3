"""DynamoDB implementations of every repository, in one table.

The A3 store (RDS is blocked on the CAB432 account). The services only see the
repository protocols, so the move back to RDS after A3 swaps these classes out.

Table layout (on-demand; string keys `pk`, `sk`):

| Item         | pk               | sk                          |
|--------------|------------------|-----------------------------|
| User         | USER#<cognito>   | USER                        |
| Organisation | ORG#<org>        | ORG                         |
| Campaign     | ORG#<org>        | CAMPAIGN#<id>               |
| Creator      | ORG#<org>        | CREATOR#<id>                |
| Assignment   | ORG#<org>        | ASSIGN#<campaign>#<creator> |
| Post         | ORG#<org>        | POST#<id>                   |

Everything an organisation owns shares its partition, so every request is a
key lookup or a Query on one partition, and scoping by organisation is built
into the key. Reads are strongly consistent. The one cross-organisation read,
the scheduled sync fan-out, uses the sparse `gsi1` index (only assignments set
`gsi1pk`), so nothing ever Scans the table.

Lists are filtered in code within the partition (e.g. a creator's
assignments). That's fine at A3 scale: an organisation holds hundreds of items,
not millions.
"""

import types
import uuid
from collections.abc import Iterator
from dataclasses import fields, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from hookd_core.enums import CampaignStatus, Platform
from hookd_core.repositories.assignments import Assignment
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.creators import Creator
from hookd_core.repositories.posts import Post, post_id
from hookd_core.repositories.users import Organisation, User

GSI1 = "gsi1"
ASSIGNMENTS_GSI1PK = "ASSIGNMENT"


def _now() -> datetime:
    return datetime.now(UTC)


def _org(organisation_id: uuid.UUID) -> str:
    return f"ORG#{organisation_id}"


# --- Table ---


def create_table(dynamodb: Any, name: str) -> Any:
    """Create the table if it doesn't exist (local development and tests).

    In AWS, Terraform creates it with the same schema. `dynamodb` is a boto3
    DynamoDB service resource.
    """
    client = dynamodb.meta.client
    try:
        client.describe_table(TableName=name)
    except client.exceptions.ResourceNotFoundException:
        _create(client, name)
    return dynamodb.Table(name)


def _create(client: Any, name: str) -> None:
    try:
        client.create_table(
            TableName=name,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": a, "AttributeType": "S"} for a in ("pk", "sk", "gsi1pk", "gsi1sk")
            ],
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": GSI1,
                    "KeySchema": [
                        {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
    except client.exceptions.ResourceInUseException:
        pass  # the API and worker both started and the other one won
    client.get_waiter("table_exists").wait(TableName=name)


# --- Dataclass <-> item ---


def _encode(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):  # datetime first: it's a date subclass
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple | list):
        return [_encode(v) for v in value]
    return value


def to_item(obj: Any, **keys: str) -> dict[str, Any]:
    """A dataclass as a DynamoDB item, plus its key attributes."""
    item = {f.name: _encode(getattr(obj, f.name)) for f in fields(obj)}
    return {**item, **keys}


def _decode(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):  # X | None
        inner = next(a for a in get_args(annotation) if a is not type(None))
        return _decode(inner, value)
    if origin is tuple:
        return tuple(_decode(get_args(annotation)[0], v) for v in value)
    if annotation is uuid.UUID:
        return uuid.UUID(value)
    if annotation is datetime:
        return datetime.fromisoformat(value)
    if annotation is date:
        return date.fromisoformat(value)
    if annotation is bool:
        return bool(value)
    if annotation is int:
        return int(value)  # numbers come back as Decimal
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if isinstance(value, Decimal):
        return int(value)
    return value


def from_item[T](cls: type[T], item: dict[str, Any]) -> T:
    hints = get_type_hints(cls)
    return cls(
        **{f.name: _decode(hints[f.name], item[f.name]) for f in fields(cls) if f.name in item}
    )  # type: ignore[arg-type]


class _Table:
    """Small helpers over a boto3 Table, shared by the repositories."""

    def __init__(self, table: Any) -> None:
        self.table = table

    def get(self, pk: str, sk: str) -> dict[str, Any] | None:
        return self.table.get_item(Key={"pk": pk, "sk": sk}, ConsistentRead=True).get("Item")

    def query_prefix(self, pk: str, sk_prefix: str) -> Iterator[dict[str, Any]]:
        yield from self._paginate(
            KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with(sk_prefix),
            ConsistentRead=True,
        )

    def query_index(self, gsi1pk: str) -> Iterator[dict[str, Any]]:
        yield from self._paginate(IndexName=GSI1, KeyConditionExpression=Key("gsi1pk").eq(gsi1pk))

    def put(self, item: dict[str, Any]) -> None:
        self.table.put_item(Item=item)

    def delete(self, pk: str, sk: str) -> bool:
        response = self.table.delete_item(Key={"pk": pk, "sk": sk}, ReturnValues="ALL_OLD")
        return "Attributes" in response

    def _paginate(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        while True:
            page = self.table.query(**kwargs)
            yield from page.get("Items", [])
            if "LastEvaluatedKey" not in page:
                return
            kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


# --- Repositories ---


class DynamoCampaignRepository:
    def __init__(self, table: Any) -> None:
        self._t = _Table(table)

    @staticmethod
    def _sk(campaign_id: uuid.UUID) -> str:
        return f"CAMPAIGN#{campaign_id}"

    def add(self, campaign: Campaign) -> Campaign:
        self._t.put(to_item(campaign, pk=_org(campaign.organisation_id), sk=self._sk(campaign.id)))
        return campaign

    def get(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign | None:
        item = self._t.get(_org(organisation_id), self._sk(campaign_id))
        return from_item(Campaign, item) if item else None

    def list(
        self, organisation_id: uuid.UUID, status: CampaignStatus | None = None
    ) -> list[Campaign]:
        campaigns = [
            from_item(Campaign, i) for i in self._t.query_prefix(_org(organisation_id), "CAMPAIGN#")
        ]
        if status is not None:
            campaigns = [c for c in campaigns if c.status == status]
        return sorted(campaigns, key=lambda c: (c.start_date, c.created_at), reverse=True)

    def save(self, campaign: Campaign) -> Campaign:
        return self.add(replace(campaign, updated_at=_now()))

    def delete(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> bool:
        return self._t.delete(_org(organisation_id), self._sk(campaign_id))


class DynamoCreatorRepository:
    def __init__(self, table: Any) -> None:
        self._t = _Table(table)

    @staticmethod
    def _sk(creator_id: uuid.UUID) -> str:
        return f"CREATOR#{creator_id}"

    def add(self, creator: Creator) -> Creator:
        self._t.put(to_item(creator, pk=_org(creator.organisation_id), sk=self._sk(creator.id)))
        return creator

    def get(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> Creator | None:
        item = self._t.get(_org(organisation_id), self._sk(creator_id))
        return from_item(Creator, item) if item else None

    def get_by_handle(
        self, organisation_id: uuid.UUID, platform: Platform, handle: str
    ) -> Creator | None:
        return next(
            (
                c
                for c in self.list(organisation_id)
                if c.platform == platform and c.handle == handle
            ),
            None,
        )

    def list(self, organisation_id: uuid.UUID) -> list[Creator]:
        creators = [
            from_item(Creator, i) for i in self._t.query_prefix(_org(organisation_id), "CREATOR#")
        ]
        return sorted(creators, key=lambda c: (c.name.lower(), c.handle))

    def save(self, creator: Creator) -> Creator:
        return self.add(replace(creator, updated_at=_now()))

    def delete(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> bool:
        return self._t.delete(_org(organisation_id), self._sk(creator_id))


class DynamoAssignmentRepository:
    def __init__(self, table: Any) -> None:
        self._t = _Table(table)

    @staticmethod
    def _sk(campaign_id: uuid.UUID, creator_id: uuid.UUID) -> str:
        return f"ASSIGN#{campaign_id}#{creator_id}"

    def _put(self, a: Assignment) -> None:
        self._t.put(
            to_item(
                a,
                pk=_org(a.organisation_id),
                sk=self._sk(a.campaign_id, a.creator_id),
                gsi1pk=ASSIGNMENTS_GSI1PK,
                gsi1sk=f"{a.created_at.isoformat()}#{a.id}",
            )
        )

    def add_many(self, assignments: list[Assignment]) -> list[Assignment]:
        for a in assignments:
            self._put(a)
        return assignments

    def get(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> Assignment | None:
        item = self._t.get(_org(organisation_id), self._sk(campaign_id, creator_id))
        return from_item(Assignment, item) if item else None

    def list_all(self) -> list[Assignment]:
        return [from_item(Assignment, i) for i in self._t.query_index(ASSIGNMENTS_GSI1PK)]

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Assignment]:
        prefix = f"ASSIGN#{campaign_id}#" if campaign_id else "ASSIGN#"
        assignments = [
            from_item(Assignment, i) for i in self._t.query_prefix(_org(organisation_id), prefix)
        ]
        if creator_id is not None:
            assignments = [a for a in assignments if a.creator_id == creator_id]
        return sorted(assignments, key=lambda a: a.created_at)

    def save(self, assignment: Assignment) -> Assignment:
        saved = replace(assignment, updated_at=_now())
        self._put(saved)
        return saved

    def delete(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> bool:
        return self._t.delete(_org(organisation_id), self._sk(campaign_id, creator_id))

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        doomed = self.list(organisation_id, campaign_id=campaign_id, creator_id=creator_id)
        for a in doomed:
            self.delete(organisation_id, a.campaign_id, a.creator_id)
        return len(doomed)


class DynamoPostRepository:
    def __init__(self, table: Any) -> None:
        self._t = _Table(table)

    @staticmethod
    def _sk(post_id_: uuid.UUID) -> str:
        return f"POST#{post_id_}"

    def add(self, post: Post) -> Post:
        self._t.put(to_item(post, pk=_org(post.organisation_id), sk=self._sk(post.id)))
        return post

    def get(self, organisation_id: uuid.UUID, post_id_: uuid.UUID) -> Post | None:
        item = self._t.get(_org(organisation_id), self._sk(post_id_))
        return from_item(Post, item) if item else None

    def get_by_external_id(
        self,
        organisation_id: uuid.UUID,
        creator_id: uuid.UUID,
        platform: Platform,
        external_id: str,
    ) -> Post | None:
        return self.get(
            organisation_id, post_id(organisation_id, creator_id, platform, external_id)
        )

    def _all(self, organisation_id: uuid.UUID) -> list[Post]:
        return [from_item(Post, i) for i in self._t.query_prefix(_org(organisation_id), "POST#")]

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Post]:
        posts = [
            p
            for p in self._all(organisation_id)
            if not p.removed
            and (campaign_id is None or p.campaign_id == campaign_id)
            and (creator_id is None or p.creator_id == creator_id)
        ]
        return sorted(posts, key=lambda p: p.posted_at, reverse=True)

    def save(self, post: Post) -> Post:
        return self.add(replace(post, updated_at=_now()))

    def delete(self, organisation_id: uuid.UUID, post_id_: uuid.UUID) -> bool:
        return self._t.delete(_org(organisation_id), self._sk(post_id_))

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        doomed = [
            p
            for p in self._all(organisation_id)
            if (campaign_id is None or p.campaign_id == campaign_id)
            and (creator_id is None or p.creator_id == creator_id)
        ]
        for p in doomed:
            self.delete(organisation_id, p.id)
        return len(doomed)


class DynamoUserRepository:
    def __init__(self, table: Any) -> None:
        self._t = _Table(table)

    @staticmethod
    def _pk(cognito_sub: str) -> str:
        return f"USER#{cognito_sub}"

    def get_by_cognito_sub(self, cognito_sub: str) -> User | None:
        item = self._t.get(self._pk(cognito_sub), "USER")
        return from_item(User, item) if item else None

    def create(self, user: User, organisation: Organisation) -> User:
        # The organisation first: if we lose the race, it's an unused item, never a
        # user pointing at a missing organisation
        self._t.put(to_item(organisation, pk=_org(organisation.id), sk="ORG"))
        try:
            self._t.table.put_item(
                Item=to_item(user, pk=self._pk(user.cognito_sub), sk="USER"),
                ConditionExpression="attribute_not_exists(pk)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
            existing = self.get_by_cognito_sub(user.cognito_sub)
            if existing is None:
                raise
            return existing
        return user
