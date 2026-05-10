"""`reddi inbox` — read inbox messages and comment replies."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out


@click.group("inbox")
def inbox_group() -> None:
    """Read your Reddit inbox (messages, comment replies, mentions)."""


@inbox_group.command("list")
@click.option(
    "--unread/--all",
    default=True,
    show_default=True,
    help="Default: only unread. Use --all to list everything.",
)
@click.option("--limit", default=20, show_default=True, help="Max items to fetch.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def list_inbox(unread: bool, limit: int, as_json: bool) -> None:
    """List inbox items.

    \b
    Examples:
      reddi inbox list                    # unread items
      reddi inbox list --all --limit 50   # last 50 items, read or unread
      reddi inbox list --json | jq        # script against the output
    """
    reddit = auth.get_authed_reddit()
    stream = reddit.inbox.unread(limit=limit) if unread else reddit.inbox.all(limit=limit)

    rows = []
    for item in stream:
        rows.append(
            {
                "id": item.id,
                "type": _item_type(item),
                "from": (item.author.name if item.author else "[reddit]"),
                "sub": getattr(item, "subreddit", None) and item.subreddit.display_name,
                "subject": _subject(item),
                "age": out.fmt_age(item.created_utc),
                "unread": item.new,
            }
        )

    out.emit(
        rows,
        json=as_json,
        table_columns=["id", "type", "from", "sub", "subject", "age", "unread"],
    )


@inbox_group.command("mark-read")
@click.option("--id", "item_ids", multiple=True, help="Item IDs to mark read (repeatable).")
@click.option("--all", "all_unread", is_flag=True, help="Mark every unread item read.")
def mark_read(item_ids: tuple[str, ...], all_unread: bool) -> None:
    """Mark inbox items as read.

    Either pass --id one or more times, or --all to mark every unread item.
    """
    if not item_ids and not all_unread:
        out.err("Pass --id <id> (repeatable) or --all.")
        raise SystemExit(2)

    reddit = auth.get_authed_reddit()

    if all_unread:
        items = list(reddit.inbox.unread(limit=None))
        if not items:
            out.info("inbox is already empty")
            return
        reddit.inbox.mark_read(items)
        out.console.print(f"[green]✓[/green] marked {len(items)} item(s) read")
        return

    # Specific IDs
    items = []
    for item_id in item_ids:
        # Reddit API: t1_ prefix for comments, t4_ for messages
        if item_id.startswith("t1_"):
            items.append(reddit.comment(id=item_id[3:]))
        elif item_id.startswith("t4_"):
            items.append(reddit.inbox.message(item_id[3:]))
        else:
            # Heuristic: try comment first, then message
            try:
                c = reddit.comment(id=item_id)
                _ = c.body  # force fetch to validate
                items.append(c)
            except Exception:
                items.append(reddit.inbox.message(item_id))

    reddit.inbox.mark_read(items)
    out.console.print(f"[green]✓[/green] marked {len(items)} item(s) read")


def _item_type(item) -> str:  # noqa: ANN001
    """Distinguish comment-reply vs username-mention vs private-message."""
    cls = type(item).__name__
    if cls == "Comment":
        # Comment in inbox = either a reply to your comment, or a mention
        return "mention" if getattr(item, "type", "") == "username_mention" else "reply"
    if cls == "Message":
        return "message"
    return cls.lower()


def _subject(item) -> str:  # noqa: ANN001
    s = getattr(item, "subject", None) or getattr(item, "link_title", "") or item.body[:60]
    return s[:80]
