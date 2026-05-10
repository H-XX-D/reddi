"""`reddi flairs` — list available flairs for a subreddit."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out


@click.command("flairs")
@click.argument("sub")
@click.option(
    "--user/--link",
    default=False,
    show_default=True,
    help="--link (default) shows post flairs; --user shows user flairs.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def flairs(sub: str, user: bool, as_json: bool) -> None:
    """List available flair templates for a subreddit.

    Use the listed `id` value as `--flair-id` when posting:

    \b
      reddi flairs SideProject
      reddi post --sub SideProject --title ... --flair-id <id>
    """
    reddit = auth.get_authed_reddit()
    sub = sub.removeprefix("r/").removeprefix("/r/")
    sr = reddit.subreddit(sub)

    templates = sr.flair.user_templates if user else sr.flair.link_templates

    rows = []
    for t in templates:
        rows.append(
            {
                "id": t["id"],
                "text": (t.get("text") or "")[:60],
                "type": t.get("type", "—"),
                "editable": t.get("text_editable", False),
                "background": t.get("background_color", "—"),
            }
        )

    if not rows:
        out.info(
            f"r/{sub} has no {'user' if user else 'link'} flairs (or you can't list them — "
            "Reddit limits flair-template visibility to mods on some subs)."
        )
        return

    out.emit(rows, json=as_json, table_columns=["id", "text", "type", "editable"])
