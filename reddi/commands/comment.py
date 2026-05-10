"""`reddi comment` — post a comment on a submission or reply to a comment."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from .. import auth
from .. import output as out

# /comments/<post>/<slug>/<comment>/ — when a comment is in the URL, it's the last bit
_COMMENT_URL_RE = re.compile(r"/comments/([a-z0-9]+)/[^/]*/([a-z0-9]+)/?$")
_SUBMISSION_URL_RE = re.compile(r"/comments/([a-z0-9]+)")


@click.command("comment")
@click.argument("target_url_or_id")
@click.option("--body", "body_text", help="Comment body text.")
@click.option(
    "--body-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Read comment body from a file.",
)
@click.option("--dry-run", is_flag=True, help="Show what would post without submitting.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def comment(
    target_url_or_id: str,
    body_text: str | None,
    body_file: Path | None,
    dry_run: bool,
    as_json: bool,
) -> None:
    """Post a comment on a submission, or reply to a comment.

    \b
    Submission URL  -> top-level comment on that post:
      reddi comment https://reddit.com/r/x/comments/abc/title/ --body "..."

    \b
    Comment URL     -> reply to that comment:
      reddi comment https://reddit.com/r/x/comments/abc/title/def/ --body "..."

    \b
    Body can come from --body or --body-file (one or the other, not both).
    Use --body - to read from stdin.
    """
    if body_text and body_file:
        out.err("--body and --body-file are mutually exclusive")
        raise SystemExit(2)

    if body_text == "-":
        body = sys.stdin.read()
    elif body_text is not None:
        body = body_text
    elif body_file is not None:
        body = body_file.read_text()
    else:
        out.err("Pass --body TEXT, --body-file PATH, or --body - (stdin).")
        raise SystemExit(2)

    if not body.strip():
        out.err("Comment body is empty.")
        raise SystemExit(2)

    target_kind, target_id = _classify_target(target_url_or_id)

    if dry_run:
        out.emit(
            {
                "target_kind": target_kind,
                "target_id": target_id,
                "body_chars": len(body),
                "preview": body[:120] + ("…" if len(body) > 120 else ""),
            },
            json=as_json,
        )
        out.info("(dry run — not submitted)")
        return

    reddit = auth.get_authed_reddit()
    if target_kind == "comment":
        target = reddit.comment(id=target_id)
    else:
        target = reddit.submission(id=target_id)

    posted = target.reply(body)
    if posted is None:
        out.err("Reddit returned no comment object — submission may be locked or archived.")
        raise SystemExit(1)

    out.emit(
        {
            "id": posted.id,
            "url": f"https://reddit.com{posted.permalink}",
            "parent": target_id,
            "parent_kind": target_kind,
        },
        json=as_json,
    )


def _classify_target(url_or_id: str) -> tuple[str, str]:
    """Return (kind, id) where kind is 'submission' or 'comment'."""
    m = _COMMENT_URL_RE.search(url_or_id)
    if m:
        return ("comment", m.group(2))
    m = _SUBMISSION_URL_RE.search(url_or_id)
    if m:
        return ("submission", m.group(1))
    # Bare ID — assume submission unless prefixed with t1_ (comment) or t3_ (submission)
    if url_or_id.startswith("t1_"):
        return ("comment", url_or_id[3:])
    if url_or_id.startswith("t3_"):
        return ("submission", url_or_id[3:])
    return ("submission", url_or_id)
