"""`reddi subs` — list and inspect subreddits."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out


@click.group("subs")
def subs_group() -> None:
    """List, inspect, and manage subreddit subscriptions."""


@subs_group.command("list")
@click.option("--limit", default=200, show_default=True, help="Max subs to fetch.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def list_subs(limit: int, as_json: bool) -> None:
    """List subreddits you're subscribed to."""
    reddit = auth.get_authed_reddit()
    rows = []
    for sr in reddit.user.subreddits(limit=limit):
        rows.append(
            {
                "name": sr.display_name,
                "subscribers": sr.subscribers,
                "nsfw": sr.over18,
                "title": (sr.title or "")[:60],
            }
        )
    rows.sort(key=lambda r: r["subscribers"] or 0, reverse=True)
    out.emit(rows, json=as_json, table_columns=["name", "subscribers", "nsfw", "title"])


@subs_group.command("info")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def sub_info(name: str, as_json: bool) -> None:
    """Show info about a subreddit."""
    reddit = auth.get_authed_reddit()
    name = name.removeprefix("r/").removeprefix("/r/")
    sr = reddit.subreddit(name)
    data = {
        "name": sr.display_name,
        "title": sr.title,
        "description": (sr.public_description or "")[:200],
        "subscribers": sr.subscribers,
        "active_users": sr.accounts_active,
        "nsfw": sr.over18,
        "created": out.fmt_age(sr.created_utc),
        "type": sr.subreddit_type,
        "submission_type": sr.submission_type,
        "url": f"https://reddit.com/r/{sr.display_name}",
    }
    out.emit(data, json=as_json)


@subs_group.command("subscribe")
@click.argument("name")
def subscribe(name: str) -> None:
    """Subscribe to a subreddit."""
    reddit = auth.get_authed_reddit()
    name = name.removeprefix("r/").removeprefix("/r/")
    reddit.subreddit(name).subscribe()
    out.console.print(f"[green]✓[/green] subscribed to r/{name}")


@subs_group.command("unsubscribe")
@click.argument("name")
def unsubscribe(name: str) -> None:
    """Unsubscribe from a subreddit."""
    reddit = auth.get_authed_reddit()
    name = name.removeprefix("r/").removeprefix("/r/")
    reddit.subreddit(name).unsubscribe()
    out.console.print(f"[green]✓[/green] unsubscribed from r/{name}")
