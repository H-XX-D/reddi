"""Smoke tests — these don't hit the Reddit API, just verify the CLI surface
loads, help renders, and the URL/argument parsing helpers behave."""

from __future__ import annotations

from click.testing import CliRunner

from reddi import __version__
from reddi.cli import cli
from reddi.commands.comment import _classify_target
from reddi.commands.status import _extract_submission_id

# ---------- entry-point + help loading ----------

def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_is_v1() -> None:
    """Lock the major-version contract: 1.x must claim v1."""
    assert __version__.startswith("1.")


def test_help_lists_every_v1_command() -> None:
    """If a v1 command is missing from `reddi --help`, the user can't discover it."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for cmd in (
        "auth",
        "me",
        "post",
        "status",
        "watch",
        "inbox",
        "comment",
        "search",
        "subs",
        "crosspost",
        "flairs",
    ):
        assert cmd in result.output, f"command '{cmd}' missing from top-level help"


def test_each_command_help_loads() -> None:
    """Every command's --help should render without crashing (catches typos in docstrings)."""
    runner = CliRunner()
    for cmd in (
        ["auth", "--help"],
        ["auth", "login", "--help"],
        ["me", "--help"],
        ["post", "--help"],
        ["status", "--help"],
        ["watch", "--help"],
        ["inbox", "--help"],
        ["inbox", "list", "--help"],
        ["inbox", "mark-read", "--help"],
        ["comment", "--help"],
        ["search", "--help"],
        ["subs", "--help"],
        ["subs", "list", "--help"],
        ["subs", "info", "--help"],
        ["crosspost", "--help"],
        ["flairs", "--help"],
    ):
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0, f"--help failed for: {' '.join(cmd)}"


# ---------- dry-run / no-network paths ----------

def test_post_dry_run_no_auth() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["post", "--sub", "test", "--title", "smoke", "--body", "hi", "--dry-run", "--json"],
    )
    assert result.exit_code == 0
    assert '"sub": "test"' in result.output
    assert '"title": "smoke"' in result.output


def test_comment_dry_run_no_auth() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "comment",
            "https://reddit.com/r/x/comments/abc/title/",
            "--body",
            "thanks",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"target_kind": "submission"' in result.output
    assert '"target_id": "abc"' in result.output


def test_comment_dry_run_on_comment_url() -> None:
    """Comment URL (with the trailing comment-id segment) classifies as 'comment'."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "comment",
            "https://reddit.com/r/x/comments/abc/title/def/",
            "--body",
            "ok",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"target_kind": "comment"' in result.output
    assert '"target_id": "def"' in result.output


def test_crosspost_dry_run_no_auth() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "crosspost",
            "https://reddit.com/r/x/comments/abc/title/",
            "--to",
            "MacApps",
            "--title",
            "different angle",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"target_sub": "MacApps"' in result.output
    assert '"source_id": "abc"' in result.output


# ---------- argument validation ----------

def test_post_url_and_body_mutually_exclusive() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["post", "--sub", "test", "--title", "x", "--url", "https://example.com", "--body", "hi"],
    )
    assert result.exit_code == 2


def test_comment_requires_body() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["comment", "abc", "--dry-run"])
    assert result.exit_code == 2


def test_comment_body_text_and_file_mutually_exclusive(tmp_path) -> None:
    body_file = tmp_path / "b.md"
    body_file.write_text("hello")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["comment", "abc", "--body", "x", "--body-file", str(body_file), "--dry-run"],
    )
    assert result.exit_code == 2


def test_inbox_mark_read_requires_target() -> None:
    """Pass neither --id nor --all -> reject."""
    runner = CliRunner()
    result = runner.invoke(cli, ["inbox", "mark-read"])
    assert result.exit_code == 2


# ---------- URL classification helpers ----------

def test_extract_submission_id_url() -> None:
    sid = _extract_submission_id("https://reddit.com/r/SideProject/comments/abc123/some-title/")
    assert sid == "abc123"


def test_extract_submission_id_bare() -> None:
    assert _extract_submission_id("abc123") == "abc123"
    assert _extract_submission_id("t3_abc123") == "abc123"


def test_classify_target_submission_url() -> None:
    kind, sid = _classify_target("https://reddit.com/r/x/comments/abc123/title/")
    assert kind == "submission"
    assert sid == "abc123"


def test_classify_target_comment_url() -> None:
    kind, cid = _classify_target("https://reddit.com/r/x/comments/abc123/title/def456/")
    assert kind == "comment"
    assert cid == "def456"


def test_classify_target_t1_t3_prefixes() -> None:
    assert _classify_target("t1_xyz") == ("comment", "xyz")
    assert _classify_target("t3_xyz") == ("submission", "xyz")
    assert _classify_target("xyz") == ("submission", "xyz")


# ---------- sub prefix stripping ----------

def test_sub_strips_r_prefix_in_post() -> None:
    runner = CliRunner()
    common = ["post", "--title", "t", "--body", "b", "--dry-run", "--json"]
    r1 = runner.invoke(cli, [*common, "--sub", "r/test"])
    r2 = runner.invoke(cli, [*common, "--sub", "test"])
    assert r1.exit_code == 0 and r2.exit_code == 0
    assert '"sub": "test"' in r1.output
    assert '"sub": "test"' in r2.output


def test_sub_strips_r_prefix_in_crosspost() -> None:
    runner = CliRunner()
    common = ["crosspost", "abc123", "--dry-run", "--json"]
    r1 = runner.invoke(cli, [*common, "--to", "r/MacApps"])
    r2 = runner.invoke(cli, [*common, "--to", "MacApps"])
    assert r1.exit_code == 0 and r2.exit_code == 0
    assert '"target_sub": "MacApps"' in r1.output
    assert '"target_sub": "MacApps"' in r2.output


# ---------- search arg validation ----------

def test_search_rejects_invalid_sort() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "anything", "--sort", "bogus"])
    assert result.exit_code == 2


def test_search_rejects_invalid_time() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "anything", "--time", "decade"])
    assert result.exit_code == 2
