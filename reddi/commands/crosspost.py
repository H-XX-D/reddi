"""`reddi crosspost` — crosspost a submission to another subreddit."""

from __future__ import annotations

import click

from .. import auth
from .. import output as out
from .status import _extract_submission_id


@click.command("crosspost")
@click.argument("source_url_or_id")
@click.option("--to", "target_sub", required=True, help="Destination subreddit.")
@click.option("--title", help="Optional new title (default: keep original title).")
@click.option("--flair-id", help="Flair template ID for the destination sub.")
@click.option("--flair-text", help="Flair text override.")
@click.option(
    "--nsfw/--no-nsfw",
    default=None,
    help="Override NSFW flag (default: inherit from source).",
)
@click.option(
    "--spoiler/--no-spoiler",
    default=None,
    help="Override spoiler flag.",
)
@click.option(
    "--send-replies/--no-send-replies",
    default=True,
    help="Receive inbox replies for the crosspost.",
)
@click.option("--dry-run", is_flag=True, help="Show what would be posted without submitting.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def crosspost(
    source_url_or_id: str,
    target_sub: str,
    title: str | None,
    flair_id: str | None,
    flair_text: str | None,
    nsfw: bool | None,
    spoiler: bool | None,
    send_replies: bool,
    dry_run: bool,
    as_json: bool,
) -> None:
    """Crosspost an existing submission to another subreddit.

    \b
    Examples:
      reddi crosspost https://reddit.com/r/SideProject/comments/abc/title/ \\
        --to MacApps
      reddi crosspost abc123 --to ObsidianMD --title "Different angle for this audience"
    """
    src_id = _extract_submission_id(source_url_or_id)
    target_sub = target_sub.removeprefix("r/").removeprefix("/r/")

    if dry_run:
        out.emit(
            {
                "source_id": src_id,
                "target_sub": target_sub,
                "title_override": title,
                "flair_id": flair_id,
                "nsfw_override": nsfw,
                "spoiler_override": spoiler,
            },
            json=as_json,
        )
        out.info("(dry run — not submitted)")
        return

    reddit = auth.get_authed_reddit()
    src = reddit.submission(id=src_id)

    kwargs = {"subreddit": target_sub, "send_replies": send_replies}
    if title:
        kwargs["title"] = title
    if flair_id:
        kwargs["flair_id"] = flair_id
    if flair_text:
        kwargs["flair_text"] = flair_text
    if nsfw is not None:
        kwargs["nsfw"] = nsfw
    if spoiler is not None:
        kwargs["spoiler"] = spoiler

    crossposted = src.crosspost(**kwargs)
    out.emit(
        {
            "id": crossposted.id,
            "url": f"https://reddit.com{crossposted.permalink}",
            "shortlink": crossposted.shortlink,
            "target_sub": target_sub,
            "source_id": src_id,
        },
        json=as_json,
    )
