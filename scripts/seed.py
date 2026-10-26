# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "boto3>=1.35", "pycognito>=2024.5"]
# ///
"""Seed a demo account with campaigns, creators, assignments and posts.

Also the A3 demo fallback if TikTok API access is not granted (see plan section 12).

Everything goes through the API as the signed-in user, so it works against any
storage (in-memory, DynamoDB Local, AWS) and exercises the real code paths:
create campaigns and creators, assign them with targets, then "Sync now" pulls
posts (fake ones when TIKTOK_MODE=mock) and one post is added by hand.

    # Create the Cognito user too (needs admin access: aws sso login --profile CAB432)
    uv run scripts/seed.py --create-user --aws-profile CAB432

    # Or seed an account you already signed up with in the web app
    uv run scripts/seed.py --email you@example.com --password '...'

    # Wipe that account's campaigns and creators first, then seed again
    uv run scripts/seed.py --reset

    # Load test account (load@hookd.test): the demo data plus 300 generated creators
    # on one always-on campaign, for scripts/load_test.py
    uv run scripts/seed.py --create-user --aws-profile CAB432 --load 300

Cognito ids come from COGNITO_USER_POOL_ID / COGNITO_APP_CLIENT_ID (env or .env).
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx

DEFAULT_EMAIL = "demo@hookd.test"
LOAD_EMAIL = "load@hookd.test"  # default account with --load
DEFAULT_PASSWORD = "HookdDemo2026"
DEFAULT_NAME = "Demo Manager"

# (name, handle, niche)
CREATORS = [
    ("Ava Thompson", "avamakesthings", "Beauty"),
    ("Liam Chen", "liamlifts", "Fitness"),
    ("Priya Nair", "priyaeats", "Food"),
    ("Jordan Blake", "jordanblakeugc", "Lifestyle"),
    ("Mia Rossi", "mia.rossi", "Beauty"),
    ("Noah Williams", "noahstudies", "Study"),
    ("Zara Ahmed", "zarastyles", "Fashion"),
    ("Ethan Park", "ethanpark.tech", "Tech"),  # on the roster, not on any campaign
]

# key -> (name, brand, start offset, end offset, hashtags), offsets in days from today
CAMPAIGNS = {
    "glow": ("Glow Serum Launch", "Lumi Skin", -21, 14, ["lumiglow", "lumiskin"]),
    "stride": ("Spring Activewear Drop", "Stride Co", -10, 40, ["stridespring"]),
    "notely": ("Back to Uni Bundle", "Notely", -55, -12, ["notelybts"]),
    "blendr": ("Summer Smoothie Series", "Blendr", 7, 60, ["blendrsummer"]),
    "bean": ("Winter Coffee Collab", "Bean There", -50, -20, ["beantherewinter"]),
}

# campaign key -> [(handle, target posts, period)]; mixed so some creators are behind
ASSIGNMENTS = {
    "glow": [
        ("avamakesthings", 2, "week"),
        ("mia.rossi", 3, "week"),
        ("jordanblakeugc", 8, "month"),
    ],
    "stride": [("liamlifts", 3, "week"), ("zarastyles", 2, "week"), ("jordanblakeugc", 1, "week")],
    "notely": [("noahstudies", 2, "week"), ("priyaeats", 4, "month")],
    "blendr": [("priyaeats", 2, "week"), ("liamlifts", 1, "week")],
    "bean": [("priyaeats", 4, "month"), ("avamakesthings", 4, "month")],
}

ARCHIVE = ["bean"]  # archived after its posts are synced

# With --load: generated creators all on this campaign, each 3 posts a week
LOAD_CAMPAIGN = ("Always-On Creator Network", "Hookd Load Test", -20, 40, ["hookdload"])
LOAD_NICHES = ["Beauty", "Fitness", "Food", "Lifestyle", "Fashion", "Tech", "Study", "Travel"]
MAX_ASSIGN_AT_ONCE = 100  # the API's limit per assign call


def read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")
    return values


def setting(name: str) -> str:
    dotenv = read_dotenv(Path(__file__).resolve().parent.parent / ".env")
    value = os.environ.get(name) or dotenv.get(name, "")
    if not value:
        sys.exit(f"Set {name} (in the environment or .env)")
    return value


def create_cognito_user(
    pool_id: str, email: str, password: str, name: str, profile: str | None
) -> None:
    """Create a confirmed user with a permanent password (no email is sent)."""
    import boto3

    region = pool_id.split("_", 1)[0]
    cognito = boto3.Session(profile_name=profile).client("cognito-idp", region_name=region)
    try:
        cognito.admin_create_user(
            UserPoolId=pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": name},
            ],
            MessageAction="SUPPRESS",
        )
        print(f"Created Cognito user {email}")
    except cognito.exceptions.UsernameExistsException:
        print(f"Cognito user {email} already exists; resetting its password")
    cognito.admin_set_user_password(
        UserPoolId=pool_id, Username=email, Password=password, Permanent=True
    )


def sign_in(pool_id: str, client_id: str, email: str, password: str) -> str:
    """Cognito access token via SRP, the same flow the web app uses."""
    from pycognito import Cognito

    user = Cognito(pool_id, client_id, user_pool_region=pool_id.split("_", 1)[0], username=email)
    user.authenticate(password=password)
    return user.access_token


def call(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, path, **kwargs)
    if response.is_error:
        sys.exit(f"{method} {path} failed ({response.status_code}): {response.text}")
    return response.json() if response.content else None


def reset(client: httpx.Client) -> None:
    for campaign in call(client, "GET", "/campaigns"):
        call(client, "DELETE", f"/campaigns/{campaign['id']}")
    for creator in call(client, "GET", "/creators"):
        call(client, "DELETE", f"/creators/{creator['id']}")


def seed(client: httpx.Client, today: date, load: int = 0) -> dict[str, Any]:
    """Create the demo workspace through the API, plus `load` generated creators on
    LOAD_CAMPAIGN. Returns what was made, for the summary."""
    generated = [
        (f"Load Creator {i}", f"load.creator{i:04d}", LOAD_NICHES[i % len(LOAD_NICHES)])
        for i in range(1, load + 1)
    ]
    creators = {}
    for n, (name, handle, niche) in enumerate(CREATORS + generated, 1):
        if generated and n % 50 == 0:
            print(f"  {n}/{len(CREATORS) + len(generated)} creators")
        created = call(
            client,
            "POST",
            "/creators",
            json={"name": name, "handle": handle, "niche": niche, "email": f"{handle}@example.com"},
        )
        creators[handle] = created["id"]

    campaigns = {}
    for key, (name, brand, start, end, hashtags) in CAMPAIGNS.items():
        created = call(
            client,
            "POST",
            "/campaigns",
            json={
                "name": name,
                "brand": brand,
                "start_date": (today + timedelta(days=start)).isoformat(),
                "end_date": (today + timedelta(days=end)).isoformat(),
                "tracking_hashtags": hashtags,
            },
        )
        campaigns[key] = created["id"]

    if generated:
        name, brand, start, end, hashtags = LOAD_CAMPAIGN
        campaigns["load"] = call(
            client,
            "POST",
            "/campaigns",
            json={
                "name": name,
                "brand": brand,
                "start_date": (today + timedelta(days=start)).isoformat(),
                "end_date": (today + timedelta(days=end)).isoformat(),
                "tracking_hashtags": hashtags,
            },
        )["id"]
        ids = [creators[handle] for _, handle, _ in generated]
        for i in range(0, len(ids), MAX_ASSIGN_AT_ONCE):
            call(
                client,
                "POST",
                f"/campaigns/{campaigns['load']}/creators",
                json={
                    "creator_ids": ids[i : i + MAX_ASSIGN_AT_ONCE],
                    "target_posts": 3,
                    "target_period": "week",
                },
            )

    for key, rows in ASSIGNMENTS.items():
        # One call per target, since a call assigns everyone with the same target
        targets: dict[tuple[int, str], list[str]] = {}
        for handle, posts, period in rows:
            targets.setdefault((posts, period), []).append(creators[handle])
        for (posts, period), creator_ids in targets.items():
            call(
                client,
                "POST",
                f"/campaigns/{campaigns[key]}/creators",
                json={"creator_ids": creator_ids, "target_posts": posts, "target_period": period},
            )

    sync = call(client, "POST", "/sync")

    # A post the sync "missed", added by link (shows up as match source: manual)
    manual = call(
        client,
        "POST",
        f"/campaigns/{campaigns['glow']}/posts",
        json={
            "url": "https://www.tiktok.com/@avamakesthings/video/7400000000000000001",
            "posted_on": (today - timedelta(days=2)).isoformat(),
            "caption": "Morning routine with the new serum #lumiglow",
            "views": 48_200,
            "likes": 3_910,
            "comments": 212,
            "shares": 140,
        },
    )

    for key in ARCHIVE:
        call(client, "POST", f"/campaigns/{campaigns[key]}/archive")

    return {"creators": creators, "campaigns": campaigns, "sync": sync, "manual_post": manual}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--email", help=f"Default {DEFAULT_EMAIL}, or {LOAD_EMAIL} with --load")
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--name", default=DEFAULT_NAME, help="Used with --create-user")
    parser.add_argument("--api-url", default="http://localhost:8000/api")
    parser.add_argument(
        "--create-user", action="store_true", help="Create the Cognito user (needs AWS admin)"
    )
    parser.add_argument("--aws-profile", help="AWS profile for --create-user, e.g. CAB432")
    parser.add_argument(
        "--reset", action="store_true", help="Delete the account's campaigns and creators first"
    )
    parser.add_argument(
        "--load",
        type=int,
        default=0,
        metavar="N",
        help="Also add N generated creators on one campaign, for scripts/load_test.py",
    )
    args = parser.parse_args()
    if not args.email:
        args.email = LOAD_EMAIL if args.load else DEFAULT_EMAIL

    pool_id = setting("COGNITO_USER_POOL_ID")
    client_id = setting("COGNITO_APP_CLIENT_ID")
    tz = ZoneInfo(os.environ.get("CAMPAIGN_TIMEZONE", "Australia/Brisbane"))

    if args.create_user:
        create_cognito_user(pool_id, args.email, args.password, args.name, args.aws_profile)
    token = sign_in(pool_id, client_id, args.email, args.password)

    with httpx.Client(
        base_url=args.api_url, headers={"Authorization": f"Bearer {token}"}, timeout=600
    ) as client:
        me = call(client, "GET", "/me")  # first call creates the user's organisation
        has_data = call(client, "GET", "/campaigns") or call(client, "GET", "/creators")
        if has_data:
            if not args.reset:
                sys.exit(f"{args.email} already has data. Run again with --reset to replace it.")
            reset(client)
        result = seed(client, datetime.now(tz).date(), args.load)

    sync = result["sync"]
    print(
        f"\nSeeded {me['email']}: {len(result['creators'])} creators, "
        f"{len(result['campaigns'])} campaigns ({len(ARCHIVE)} archived)"
        f"{f', {args.load} generated creators for load tests' if args.load else ''}\n"
        f"Sync ({sync['mode']}): {sync['creators']} creators, {sync['added']} posts added, "
        f"{len(sync['failed'])} failed; plus 1 manual post\n"
        f"\nSign in at the web app with:\n  email:    {args.email}\n  password: {args.password}"
    )


if __name__ == "__main__":
    main()
