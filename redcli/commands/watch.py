"""`redcli watch` — live-update post stats."""

from __future__ import annotations

import time
from datetime import datetime

import click
from rich.live import Live
from rich.table import Table

from .. import auth
from .. import output as out
from .status import _extract_submission_id


@click.command("watch")
@click.argument("post_url_or_id")
@click.option(
    "--interval",
    default=60,
    show_default=True,
    type=int,
    help="Refresh interval in seconds (min 30, Reddit rate limits).",
)
@click.option(
    "--once",
    is_flag=True,
    help="Refresh once and exit (useful for cron / scripted polling).",
)
def watch(post_url_or_id: str, interval: int, once: bool) -> None:
    """Live-update vote/comment stats for a post.

    Useful during a launch — pin to a second monitor and watch the post grow
    (or not) in real time. Press Ctrl-C to stop.
    """
    if interval < 30 and not once:
        out.warn("interval < 30s may hit Reddit rate limits; clamped to 30s")
        interval = 30

    sid = _extract_submission_id(post_url_or_id)
    reddit = auth.get_authed_reddit()

    def snapshot() -> Table:
        s = reddit.submission(id=sid)
        # Force a refresh on every poll
        s._fetched = False  # type: ignore[attr-defined]  # PRAW internal
        s._fetch()  # type: ignore[attr-defined]
        t = Table(show_header=False, box=None)
        t.add_column(style="bold cyan")
        t.add_column()
        t.add_row("post", s.title[:80])
        t.add_row("sub", f"r/{s.subreddit.display_name}")
        t.add_row("score", f"[bold]{s.score}[/bold] ({int(s.upvote_ratio * 100)}% upvoted)")
        t.add_row("comments", str(s.num_comments))
        t.add_row("age", out.fmt_age(s.created_utc))
        t.add_row("status", _state_str(s))
        t.add_row("checked", datetime.now().strftime("%H:%M:%S"))
        return t

    if once:
        out.console.print(snapshot())
        return

    with Live(snapshot(), console=out.console, refresh_per_second=1) as live:
        try:
            while True:
                time.sleep(interval)
                live.update(snapshot())
        except KeyboardInterrupt:
            out.console.print("\n[dim]stopped[/dim]")


def _state_str(s) -> str:  # noqa: ANN001
    flags = []
    if getattr(s, "removed_by_category", None) is not None:
        flags.append("[red]removed[/red]")
    if s.locked:
        flags.append("[yellow]locked[/yellow]")
    if s.stickied:
        flags.append("[cyan]stickied[/cyan]")
    return " ".join(flags) if flags else "[green]live[/green]"
