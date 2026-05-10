"""`reddi search` — search Reddit submissions."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out

VALID_SORTS = ("relevance", "hot", "top", "new", "comments")
VALID_TIME = ("all", "year", "month", "week", "day", "hour")


@click.command("search")
@click.argument("query")
@click.option(
    "--sub",
    help="Restrict to a specific subreddit (omit to search across all of Reddit).",
)
@click.option(
    "--sort",
    type=click.Choice(VALID_SORTS),
    default="relevance",
    show_default=True,
)
@click.option(
    "--time",
    "time_filter",
    type=click.Choice(VALID_TIME),
    default="all",
    show_default=True,
    help="Time window for top/relevance sorts.",
)
@click.option("--limit", default=25, show_default=True, help="Max results.")
@click.option(
    "--syntax",
    type=click.Choice(("lucene", "cloudsearch", "plain")),
    default="lucene",
    show_default=True,
    help="Reddit query syntax. 'lucene' supports field:value, AND/OR, etc.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def search(
    query: str,
    sub: str | None,
    sort: str,
    time_filter: str,
    limit: int,
    syntax: str,
    as_json: bool,
) -> None:
    """Search Reddit posts.

    \b
    Examples:
      reddi search "rust performance"
      reddi search "self.SideProject" --sub SideProject --sort new --limit 10
      reddi search "title:threadsaver" --sort new --limit 5
      reddi search "selftext:gh-style cli" --sub LocalLLaMA
    """
    reddit = auth.get_authed_reddit()
    if sub:
        target = reddit.subreddit(sub.removeprefix("r/").removeprefix("/r/"))
    else:
        target = reddit.subreddit("all")

    rows = []
    for s in target.search(query, sort=sort, time_filter=time_filter, limit=limit, syntax=syntax):
        rows.append(
            {
                "id": s.id,
                "sub": s.subreddit.display_name,
                "title": s.title[:80],
                "score": s.score,
                "comments": s.num_comments,
                "age": out.fmt_age(s.created_utc),
                "url": f"https://reddit.com{s.permalink}",
            }
        )

    out.emit(rows, json=as_json, table_columns=["sub", "title", "score", "comments", "age"])
