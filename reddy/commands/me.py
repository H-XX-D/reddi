"""`reddy me` — show authenticated account info."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out


@click.command("me")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def me(as_json: bool) -> None:
    """Show your Reddit account info."""
    reddit = auth.get_authed_reddit()
    user = reddit.user.me()
    if user is None:
        out.err("Could not fetch user — token may be invalid. Try `reddy auth login` again.")
        raise SystemExit(1)

    data = {
        "username": user.name,
        "id": user.id,
        "created": out.fmt_age(user.created_utc),
        "link_karma": user.link_karma,
        "comment_karma": user.comment_karma,
        "total_karma": user.link_karma + user.comment_karma,
        "is_gold": user.is_gold,
        "is_mod": user.is_mod,
        "has_verified_email": user.has_verified_email,
    }
    out.emit(data, json=as_json)
