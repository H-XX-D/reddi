# reddi

A modern command-line client for Reddit. Built for the **launch / monitor / engage** loop: write a post, watch it live, reply to comments, crosspost to the next sub — all from your shell.

```text
status:    v1.0.0 — production / stable
license:   MIT
runtime:   python 3.9+
ergonomics: gh-style
```

## Why reddi exists

If you launch products on Reddit, you're stuck in a tab-switching loop: paste post into one sub, watch the upvote count, switch to the next sub for a tailored variant, refresh inbox for replies, draft a comment, paste, repeat. The browser is fine for casual reading but terrible for that workflow.

The tools that used to help with this — Apollo, Reddit is Fun, `rtv`, `tuir` — mostly died after Reddit's 2023 API pricing change. `reddi` is the small, stable, MIT-licensed tool that fills the gap: just the slice of Reddit that survives nicely on the API, optimized for indie devs, marketers, mods, and bot operators who already live in the terminal.

## Install

```sh
pipx install reddi
```

Or from source:

```sh
git clone https://github.com/H-XX-D/reddi
cd reddi
pipx install .
```

## First-time setup

Reddit requires an "installed app" registration before you can authenticate. One-time, takes about a minute, free.

1. Go to <https://www.reddit.com/prefs/apps>
2. Click **"create another app..."** at the bottom
3. Choose type: **"installed app"**
4. Name: anything (e.g. `reddi-yourusername`)
5. Redirect URI: `http://localhost:16180/`
   *(16180 is the first five digits of the golden ratio — picked to avoid the heavy collisions on 8080/3000/5000. Use `--port` to override.)*
6. Click **"create app"**
7. Copy the client ID — the short string under your app's name (NOT the longer "secret" field)

Then:

```sh
reddi auth login --client-id YOUR_CLIENT_ID
```

A browser window opens, you approve the scopes, and `reddi` saves a refresh token to `~/.config/reddi/credentials.json` (mode 0600). One-time setup; you won't need to log in again until you `reddi auth logout`.

## The launch workflow

This is what reddi is built for. The full loop in five commands:

```sh
# 1. Find the right flair before posting
reddi flairs SideProject

# 2. Submit the post
reddi post --sub SideProject \
  --title "I built reddi: a modern Reddit CLI" \
  --body-file post.md \
  --flair-id <id-from-step-1>

# 3. Watch how it does, live
reddi watch <post-url> --interval 60

# 4. Read inbox replies as they come in
reddi inbox list

# 5. Reply to a specific comment
reddi comment <comment-url> --body "thanks for trying it!"

# 6. Crosspost to the next sub with a tailored title
reddi crosspost <post-url> --to MacApps \
  --title "[reddi] CLI for managing Reddit launches"
```

Every command takes `--json` for scripting:

```sh
reddi status <post-url> --json | jq '.score'
```

## Full command reference

```text
reddi auth login           authenticate via browser OAuth
reddi auth status          show current auth state
reddi auth logout          remove stored credentials

reddi me                   show your account info

reddi post                 submit a text or link post (--dry-run supported)
reddi status <url>         vote/comment/removed-state for a post
reddi watch <url>          live-updating dashboard

reddi inbox list           list inbox items (--unread / --all)
reddi inbox mark-read      mark items read (--id repeatable, or --all)

reddi comment <url>        post a top-level comment OR reply to a comment
reddi crosspost <url>      crosspost to another sub (--to)
reddi search <query>       search posts (--sub, --sort, --time, --limit)

reddi subs list            list your subscribed subs
reddi subs info <name>     subreddit metadata
reddi subs subscribe <name>     add subscription
reddi subs unsubscribe <name>   remove subscription

reddi flairs <sub>         list available flair templates for a sub
```

## Examples

```sh
# Lint a post before submitting
reddi post --sub test --title "smoke" --body "hi" --dry-run

# Crosspost from a different angle
reddi crosspost https://reddit.com/r/x/comments/abc/... \
  --to ObsidianMD --title "Pipe AI chats into your vault as Markdown"

# Search a sub for related discussions
reddi search "show & tell" --sub SideProject --sort new --limit 10

# Reply to the comment a user just left on your launch post
reddi comment https://reddit.com/r/x/comments/abc/title/def/ --body "thanks!"

# Watch a post during a launch (Ctrl-C to stop)
reddi watch https://reddit.com/r/SideProject/comments/abc123/...

# Mark every unread reply as read after a busy thread cooldown
reddi inbox mark-read --all

# Find a flair before posting
reddi flairs MacApps
```

## Scopes requested

By default `reddi auth login` requests:

- `identity` — read your username (for `reddi me` and the login confirmation)
- `submit` — create posts
- `read` — read posts and comments
- `save`, `subscribe`, `vote`, `edit`, `history` — common interactive actions
- `privatemessages` — for `reddi inbox`
- `mysubreddits` — for `reddi subs list`

Override with `--scope identity --scope submit` (repeatable) if you want to scope down.

## v1.0 stability contract

The v1.0 surface is the stable contract: we will not break these commands or flag shapes within the 1.x line. The full list locked in v1.0:

```text
reddi auth (login|status|logout)
reddi me
reddi post
reddi status <url-or-id>
reddi watch <url-or-id>
reddi inbox (list|mark-read)
reddi comment <url-or-id>
reddi search <query>
reddi subs (list|info|subscribe|unsubscribe)
reddi crosspost <url-or-id> --to <sub>
reddi flairs <sub>
```

`--json` output shape is part of the contract too — JSON keys won't change incompatibly within 1.x. New fields may be added, existing fields won't disappear or change semantics.

## Roadmap

- **v1.1** — `mod` commands for subreddit moderators (approve, remove, distinguish, lock, sticky)
- **v1.2** — `launch` orchestration: declare a multi-sub launch in JSON, reddi runs the schedule (post-A-now, post-B-in-2h, watch-all-for-24h, alert-on-removal)
- **v1.3** — TUI mode (`reddi tui`) for browsing
- **v2.0** — Possible Go rewrite for single-binary distribution via Homebrew

## Contributing

PRs welcome. Run tests with:

```sh
pip install -e ".[dev]"
ruff check reddi tests
pytest
```

CI runs ruff + pytest on Python 3.9 / 3.10 / 3.11 / 3.12.

## Why this exists in 2026

After the 2023 API pricing event there's a gap: no `gh`-equivalent for Reddit. PRAW is excellent as a library but doesn't give you a CLI. The popular TUIs (`rtv`, `tuir`) targeted browsing, not the launch/manage workflow that solopreneurs and indie devs actually need. `reddi` fills that gap — small, focused, stable, and shaped around the actual workflow rather than the API surface.

## License

MIT — see `LICENSE`.
