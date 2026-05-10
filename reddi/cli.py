"""reddi entry point.

The command surface intentionally mirrors `gh`'s ergonomics: top-level verbs
(post, status, watch, me), with a separate `auth` group for credentials.
"""

from __future__ import annotations

import click

from . import __version__
from .commands.auth_cmd import auth_group
from .commands.me import me as me_cmd
from .commands.post import post as post_cmd
from .commands.status import status as status_cmd
from .commands.watch import watch as watch_cmd


@click.group()
@click.version_option(version=__version__, prog_name="reddi")
def cli() -> None:
    """A modern command-line client for Reddit.

    First-time setup:

      \b
      1. Register an "installed app" at https://www.reddit.com/prefs/apps
         (redirect URI: http://localhost:16180/)
      2. reddi auth login --client-id YOUR_CLIENT_ID
      3. reddi me  # confirm it works

    Common workflows:

      \b
      reddi post --sub SideProject --title "I built X" --body-file post.md
      reddi status https://reddit.com/r/SideProject/comments/abc123/...
      reddi watch  https://reddit.com/r/SideProject/comments/abc123/...
    """


cli.add_command(auth_group)
cli.add_command(post_cmd)
cli.add_command(status_cmd)
cli.add_command(watch_cmd)
cli.add_command(me_cmd)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
