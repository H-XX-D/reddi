"""Output formatting helpers.

`gh` does this well: human-readable by default, `--json` for scripting.
We mirror that pattern.
"""

from __future__ import annotations

import json as _json
import sys
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def emit(data: Any, json: bool = False, *, table_columns: list[str] | None = None) -> None:
    """Print data either as a Rich table (human-readable) or as JSON.

    `data` should be either a single dict (-> key/value table) or a list of
    dicts (-> column table).
    """
    if json:
        _json.dump(data, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return

    if isinstance(data, list):
        if not data:
            console.print("[dim](no results)[/dim]")
            return
        cols = table_columns or list(data[0].keys())
        table = Table(show_header=True, header_style="bold cyan")
        for c in cols:
            table.add_column(c)
        for row in data:
            table.add_row(*[_render_cell(row.get(c)) for c in cols])
        console.print(table)
    elif isinstance(data, dict):
        table = Table(show_header=False, box=None)
        table.add_column(style="bold cyan")
        table.add_column()
        for k, v in data.items():
            table.add_row(k, _render_cell(v))
        console.print(table)
    else:
        console.print(str(data))


def _render_cell(v: Any) -> str:
    if v is None:
        return "[dim]—[/dim]"
    if isinstance(v, bool):
        return "[green]yes[/green]" if v else "[red]no[/red]"
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def fmt_age(unix_ts: float) -> str:
    """Render a Unix timestamp as a humanized age (e.g. '23m ago', '4h ago')."""
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def err(msg: str) -> None:
    err_console.print(f"[red]error:[/red] {msg}")


def warn(msg: str) -> None:
    err_console.print(f"[yellow]warn:[/yellow] {msg}")


def info(msg: str) -> None:
    err_console.print(f"[dim]{msg}[/dim]")
