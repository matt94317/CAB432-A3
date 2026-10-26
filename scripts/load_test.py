# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pycognito>=2024.5"]
# ///
"""Cache and load tests against a seeded account. No TikTok account needed: run the
app with TIKTOK_MODE=mock.

Seed the account first (load@hookd.test, with generated creators to sync):

    uv run scripts/seed.py --create-user --aws-profile CAB432 --load 300 --api-url URL

Then, with the same --api-url (default http://localhost:8000/api):

    # Cache: a write makes the next dashboard read a miss, then reads hit; times both
    uv run scripts/load_test.py cache

    # API scaling: concurrent dashboard and list reads as the signed-in user
    uv run scripts/load_test.py api --seconds 480 --concurrency 50

    # Worker scaling: "Sync now" a few times, queueing a real sync job per creator
    # each time (set TIKTOK_MOCK_DELAY_MS so each one takes as long as a real fetch)
    uv run scripts/load_test.py queue --rounds 3

Watch ECS tasks, queue depth and alarms meanwhile with: scripts/scaling-test.sh watch
"""

import argparse
import asyncio
import random
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass, field

import httpx
from seed import DEFAULT_PASSWORD, LOAD_EMAIL, call, setting, sign_in


def ms(seconds: float) -> str:
    return f"{seconds * 1000:.0f} ms"


def p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=20)[-1] if len(values) > 1 else values[0]


def dashboards(client: httpx.Client) -> list[tuple[str, str]]:
    """(label, path) of the cached reads: the overview, then each active campaign's
    dashboard, the one with the most creators first."""
    campaigns = [c for c in call(client, "GET", "/campaigns") if c["status"] == "active"]
    if not campaigns:
        sys.exit("No active campaigns. Seed the account first (scripts/seed.py --load 300).")
    campaigns.sort(key=lambda c: -(c["progress"] or {}).get("creators", 0))
    return [("overview", "/overview")] + [
        (c["name"], f"/campaigns/{c['id']}/dashboard") for c in campaigns
    ]


# --- cache ---


def cache_test(client: httpx.Client, rounds: int, hits: int) -> None:
    """Per round: write (invalidates the organisation's dashboards), read once (should
    miss and rebuild), then read `hits` more times (should hit)."""
    creator = call(client, "GET", "/creators")[0]
    targets = dashboards(client)[:2]  # the overview and the biggest campaign

    stale = missed = 0
    print(f"{rounds} rounds of: write, 1 read, {hits} reads\n")
    print(f"{'read':<32} {'miss p50':>9} {'hit p50':>9} {'faster':>7}  unexpected")
    for label, path in targets:
        miss_times, hit_times, unexpected = [], [], 0
        for _ in range(rounds):
            # A no-op edit still counts as a write, so it invalidates
            call(client, "PATCH", f"/creators/{creator['id']}", json={"niche": creator["niche"]})
            for i in range(hits + 1):
                started = time.perf_counter()
                response = client.get(path)
                elapsed = time.perf_counter() - started
                response.raise_for_status()
                state = response.headers.get("X-Cache")
                expected = "miss" if i == 0 else "hit"
                (miss_times if state == "miss" else hit_times).append(elapsed)
                if state != expected:
                    unexpected += 1
                    stale += i == 0  # served from cache straight after a write
                    missed += i > 0
        if not hit_times:
            sys.exit(f"\n{path} never hit the cache. Is REDIS_URL set for the API?")
        miss, hit = statistics.median(miss_times), statistics.median(hit_times)
        print(f"{label[:32]:<32} {ms(miss):>9} {ms(hit):>9} {miss / hit:>6.1f}x  {unexpected}")

    if missed:
        print(f"\n{missed} unexpected misses: the worker may have synced this account mid-test")
    if stale:
        sys.exit(f"FAIL: {stale} reads right after a write were served from the cache")
    print("OK: every read after a write rebuilt the dashboard")


# --- api ---


@dataclass
class Stats:
    times: list[float] = field(default_factory=list)
    statuses: Counter = field(default_factory=Counter)
    cache: Counter = field(default_factory=Counter)

    def line(self, seconds: float) -> str:
        errors = sum(n for s, n in self.statuses.items() if s >= 400 or s == 0)
        cached = self.cache["hit"] + self.cache["miss"]
        hit_rate = f"{self.cache['hit'] / cached:.0%}" if cached else "-"
        latency = (
            f"p50 {ms(statistics.median(self.times))}  p95 {ms(p95(self.times))}"
            if self.times
            else "no responses"
        )
        return (
            f"{len(self.times):>7} req  {len(self.times) / seconds:>6.1f}/s  {latency}  "
            f"errors {errors}  cache hits {hit_rate}"
        )


async def api_load(base_url: str, token: str, paths: list[str], seconds: int, workers: int) -> None:
    total, window = Stats(), Stats()
    deadline = time.monotonic() + seconds

    async def worker(client: httpx.AsyncClient) -> None:
        while time.monotonic() < deadline:
            path = random.choice(paths)
            started = time.perf_counter()
            try:
                response = await client.get(path)
                status = response.status_code
                cache = response.headers.get("X-Cache")
            except httpx.HTTPError:
                status, cache = 0, None
            elapsed = time.perf_counter() - started
            for stats in (total, window):
                stats.times.append(elapsed)
                stats.statuses[status] += 1
                if cache:
                    stats.cache[cache] += 1

    async def report() -> None:
        nonlocal window
        started = time.monotonic()
        while time.monotonic() < deadline:
            await asyncio.sleep(min(10, max(0, deadline - time.monotonic())))
            print(f"{time.monotonic() - started:>5.0f}s  {window.line(10)}")
            window = Stats()

    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        limits=httpx.Limits(max_connections=workers),
    ) as client:
        await asyncio.gather(report(), *(worker(client) for _ in range(workers)))

    print(f"\nTotal  {total.line(seconds)}")
    print(
        "Status codes: "
        + ", ".join(f"{s or 'network error'}: {n}" for s, n in sorted(total.statuses.items()))
    )


# --- queue ---


def queue_load(client: httpx.Client, rounds: int) -> None:
    queued = 0
    for n in range(1, rounds + 1):
        run = call(client, "POST", "/sync")
        if run["mode"] == "inline":
            print(
                f"Round {n}: synced {run['creators']} creators in the API process "
                "(SYNC_MODE=inline, so no queue or worker involved)"
            )
            continue
        queued += run["creators"]
        print(f"Round {n}: queued {run['creators']} sync jobs")
    if queued:
        print(f"\n{queued} jobs on the sync queue. Each fetches fake posts, upserts them")
        print("in DynamoDB and invalidates the cache, like a real sync.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("test", choices=["cache", "api", "queue"])
    parser.add_argument("--email", default=LOAD_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--api-url", default="http://localhost:8000/api")
    parser.add_argument("--rounds", type=int, default=None, help="cache: 5, queue: 3")
    parser.add_argument("--hits", type=int, default=5, help="cache: reads per round after the miss")
    parser.add_argument("--seconds", type=int, default=480, help="api: how long to load it")
    parser.add_argument("--concurrency", type=int, default=50, help="api: requests in flight")
    args = parser.parse_args()

    token = sign_in(
        setting("COGNITO_USER_POOL_ID"), setting("COGNITO_APP_CLIENT_ID"), args.email, args.password
    )
    print(f"{args.email} on {args.api_url}\n")

    with httpx.Client(
        base_url=args.api_url, headers={"Authorization": f"Bearer {token}"}, timeout=60
    ) as client:
        if args.test == "cache":
            cache_test(client, args.rounds or 5, args.hits)
        elif args.test == "queue":
            queue_load(client, args.rounds or 3)
        else:
            # Mostly cached dashboard reads, plus uncached lists that always hit DynamoDB
            cached = [path for _, path in dashboards(client)]
            paths = cached * 3 + ["/campaigns", "/creators", "/behind-target"]
            print(
                f"{args.concurrency} connections for {args.seconds}s over {len(cached)} cached "
                "and 3 uncached reads\n"
            )
            asyncio.run(api_load(args.api_url, token, paths, args.seconds, args.concurrency))


if __name__ == "__main__":
    main()
