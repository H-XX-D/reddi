"""`reddi devvit` — wrapper for Reddit's Devvit platform CLI.

Devvit is Reddit's *internal* app platform: TypeScript/React code that
runs on Reddit's infrastructure as custom posts, mod tools, or subreddit
widgets. It's a different system from reddi's OAuth API surface — but
both are "code that does something with Reddit," and it's useful to have
one CLI as the entry point for both.

This wrapper just shells out to `npx devvit` and `npm` in a configured
subfolder (default: ./devvit/). It's not trying to replace devvit — it's
trying to put reddi at the top of the workflow tree.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import click

from .. import output as out

DEFAULT_DEVVIT_DIR = Path("./devvit")


@click.group("devvit")
@click.option(
    "--dir",
    "devvit_dir",
    default=None,
    type=click.Path(path_type=Path),
    help="Path to the Devvit project (default: ./devvit/).",
)
@click.pass_context
def devvit_group(ctx: click.Context, devvit_dir: Path | None) -> None:
    """Wrap Reddit's Devvit platform CLI (`npx devvit`).

    \b
    Devvit is a separate system from reddi's OAuth API. Devvit apps run
    inside Reddit (custom posts, mod tools); reddi talks to Reddit from
    your shell. This command group bundles Devvit management under the
    reddi entry point so you have one CLI for both.

    \b
    Quickstart:
      reddi devvit init        # interactive scaffold (opens browser)
      reddi devvit dev         # run the Devvit dev server
      reddi devvit upload      # publish to Reddit
    """
    ctx.ensure_object(dict)
    ctx.obj["devvit_dir"] = (devvit_dir or DEFAULT_DEVVIT_DIR).resolve()


@devvit_group.command("init")
@click.option(
    "--token",
    help=(
        "Devvit creation token from https://developers.reddit.com/new. "
        "Optional — if omitted, npx devvit init runs interactively and "
        "opens your browser for auth."
    ),
)
@click.pass_context
def init(ctx: click.Context, token: str | None) -> None:
    """Scaffold a new Devvit project into ./devvit/ (or --dir).

    Equivalent to running `npx devvit init` from inside the target dir,
    with the parent dir pre-created.
    """
    target: Path = ctx.obj["devvit_dir"]
    _require_npx()

    if target.exists() and any(target.iterdir()):
        out.err(
            f"{target} already exists and is not empty. "
            "Remove it first, or pass --dir to use a different path."
        )
        raise SystemExit(2)

    target.mkdir(parents=True, exist_ok=True)
    out.console.print(f"[cyan]→[/cyan] scaffolding Devvit project in {target}")

    # If a token was passed, use `npm create devvit@latest <token>` (one-shot
    # with the React/vibe-coding template baked into the token). Otherwise
    # fall through to interactive `npx devvit init`.
    if token:
        cmd = ["npm", "create", "devvit@latest", token, "--", "--yes"]
    else:
        cmd = ["npx", "--yes", "devvit", "init"]

    out.info(f"running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=target.parent)
    if result.returncode != 0:
        out.err("devvit init failed; see output above.")
        raise SystemExit(result.returncode)
    out.console.print(f"\n[green]✓[/green] Devvit project scaffolded at {target}")


@devvit_group.command("dev")
@click.pass_context
def dev(ctx: click.Context) -> None:
    """Run the Devvit dev server (`npm run dev` inside the project dir).

    Devvit's dev server hot-reloads your app into a test subreddit so you
    can iterate in your browser.
    """
    target: Path = ctx.obj["devvit_dir"]
    _require_project(target)
    out.info(f"running: npm run dev (in {target})")
    result = subprocess.run(["npm", "run", "dev"], cwd=target)
    raise SystemExit(result.returncode)


@devvit_group.command("playtest")
@click.argument("subreddit", required=False)
@click.pass_context
def playtest(ctx: click.Context, subreddit: str | None) -> None:
    """Run `npx devvit playtest <subreddit>` — Devvit's hot-reload-to-real-sub mode.

    Without an arg, Devvit prompts for the target subreddit (must be one
    you moderate).
    """
    target: Path = ctx.obj["devvit_dir"]
    _require_project(target)
    cmd = ["npx", "devvit", "playtest"]
    if subreddit:
        cmd.append(subreddit.removeprefix("r/").removeprefix("/r/"))
    out.info(f"running: {' '.join(cmd)} (in {target})")
    result = subprocess.run(cmd, cwd=target)
    raise SystemExit(result.returncode)


@devvit_group.command("upload")
@click.pass_context
def upload(ctx: click.Context) -> None:
    """Publish the Devvit app to Reddit (`npx devvit upload`).

    First upload is interactive — Devvit asks you to confirm the app
    name, version, and category. Subsequent uploads just bump the version
    and push.
    """
    target: Path = ctx.obj["devvit_dir"]
    _require_project(target)
    out.info(f"running: npx devvit upload (in {target})")
    result = subprocess.run(["npx", "devvit", "upload"], cwd=target)
    raise SystemExit(result.returncode)


@devvit_group.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show whether the Devvit project exists, and which template it uses."""
    target: Path = ctx.obj["devvit_dir"]
    if not target.exists():
        out.console.print(
            f"[yellow]no Devvit project at {target}[/yellow] — "
            "run `reddi devvit init` to scaffold one"
        )
        raise SystemExit(1)
    pkg = target / "package.json"
    devvit_yaml = target / "devvit.yaml"
    data = {
        "path": str(target),
        "package_json": pkg.exists(),
        "devvit_yaml": devvit_yaml.exists(),
        "node_modules": (target / "node_modules").exists(),
    }
    if pkg.exists():
        try:
            import json

            with pkg.open() as f:
                p = json.load(f)
            data["name"] = p.get("name")
            data["version"] = p.get("version")
        except Exception:
            pass
    out.emit(data)


# ---------- helpers ----------

def _require_npx() -> None:
    if shutil.which("npx") is None:
        out.err(
            "npx not found on PATH. Install Node.js (https://nodejs.org) — "
            "devvit is a Node-based tool."
        )
        raise SystemExit(127)


def _require_project(path: Path) -> None:
    if not path.exists():
        out.err(
            f"No Devvit project at {path}. "
            "Run `reddi devvit init` first, or pass `--dir <existing-project>`."
        )
        raise SystemExit(2)
    if not (path / "package.json").exists():
        out.err(
            f"{path} exists but doesn't look like a Devvit project "
            "(no package.json). Check the --dir path."
        )
        raise SystemExit(2)
    # Keep os import used implicitly by future expansions; touch it to silence linters
    _ = os.environ
