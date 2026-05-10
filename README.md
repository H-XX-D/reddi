# reddi

**Turns the Reddit launch loop from 90 minutes of tab-switching into 20 minutes of terminal commands.** Built for indie devs, marketers, mods, and bot operators who post on Reddit regularly. `reddi post`, `reddi watch`, `reddi inbox list`, `reddi comment`, `reddi crosspost`, `reddi launch` — composable, scriptable, dry-runnable.

```text
status:    v1.1.0 — production / stable
license:   MIT
runtime:   python 3.9+
ergonomics: gh-style
```

Other Reddit CLIs (`rtv`, `tuir`, `reddix`, `rdt-cli`) optimize for *browsing without a browser*. **reddi optimizes for acting on Reddit efficiently from your shell** — different goal, different design.

## What that means concretely

| Workflow step | Browser | reddi |
|---|---|---|
| Lint a post before submitting | not possible | `reddi post ... --dry-run --json` |
| Monitor a post live | refresh every 30s | `reddi watch <url>` |
| Reply to a comment | tab → click → click → type → submit | `reddi comment <url> --body-file reply.md` |
| Crosspost with new title | open post → click crosspost → edit → submit | `reddi crosspost <url> --to MacApps --title "..."` |
| Launch 5 subs over 6 hours | 5 manual rounds | `reddi launch launch.json` (declarative, runs unattended) |
| Detect post removal | refresh, look for "[removed]" | `reddi watch <url> --on-removal "notify-send 'removed'"` |
| Stream new inbox replies live | F5 the inbox | `reddi inbox watch` |
| Find your removed posts | scroll your profile | `reddi history --json \| jq '.[] \| select(.removed)'` |

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

reddi needs Reddit OAuth credentials. The Reddit side is a one-time form, but Reddit has a few gates that bounce a lot of first-time users — so do the *pre-flight check* first.

### Pre-flight (clears 90% of "create app" blocks)

Before going to the app form, make sure your Reddit account has these:

1. **Verified email.** Go to <https://www.reddit.com/settings/account>. If "Email" doesn't say "verified," click the verification button and click the link in your inbox. This is the single most common cause of being blocked from app creation.
2. **Account in good standing.** No active suspensions / shadowbans. Check by browsing <https://www.reddit.com/> while logged in — if you can see your own posts and karma, you're fine.
3. **(Optional but recommended) verified phone number.** Some account vintages need this for developer access. Same settings page.

If all three are green, you'll have access to the app form. If not, fix them first — none of the workarounds below help if Reddit's account-level gates aren't cleared.

### Create the app

1. Go to <https://www.reddit.com/prefs/apps>
2. Scroll to the **bottom** of the page and click **"create another app..."** (or "are you a developer? create an app..." if it's your first time)
3. Fill in the form:
   - **name:** anything (e.g. `reddi-yourusername`)
   - **type:** select the **"installed app"** radio button (NOT "script", NOT "web app")
   - **redirect uri:** `http://127.0.0.1:16180/`
     *(use `127.0.0.1` rather than `localhost` — some Reddit accounts hit a "redirect uri must be a non-localhost URL" policy check that `127.0.0.1` passes universally; trailing slash matters; `http://` not `https://`)*
   - **about url / description:** leave blank
4. Click **"create app"**
5. Your app appears with the **client ID** as a short alphanumeric string (~14 chars) right under the app name. That's what you need. NOT the longer "secret" field (we don't use it for installed-app type).

### Authenticate

```sh
reddi auth login --client-id YOUR_CLIENT_ID --host 127.0.0.1
```

(Omit `--host 127.0.0.1` if you registered with `localhost` instead.)

A browser window opens to Reddit's authorize page → you click **"Allow"** → Reddit redirects to your local reddi server → reddi captures the OAuth code → saves a refresh token to `~/.config/reddi/credentials.json` (mode 0600).

Verify it worked:

```sh
reddi auth status
reddi me
```

You should see your username, karma, and account info.

### Troubleshooting

**"Responsible Builder Policy" banner / notice when you visit /prefs/apps**

This is usually informational — you can scroll past it and the form still works. If the form is greyed out or refuses submission, it means your account hasn't met the policy prerequisites. Most common fix: verify your email (above). Sometimes you also need to log into <https://developers.reddit.com> once to trigger an account-level "accept developer terms" flow.

**"Redirect URI must be a non-localhost URL" rejection**

Re-register the app with `http://127.0.0.1:16180/` instead of `http://localhost:16180/`. Same loopback address, different string that Reddit's validator accepts universally. Then run `reddi auth login` with `--host 127.0.0.1`.

**Browser opens but Reddit shows "redirect_uri does not match"**

The redirect URI in your Reddit app registration must be a byte-exact match for what reddi sends. Common mismatches:

| You registered | reddi sends | Fix |
|---|---|---|
| `http://localhost:8080/` | `http://localhost:16180/` | re-register with port 16180, OR run `reddi auth login --port 8080` |
| `http://localhost:16180` (no trailing slash) | `http://localhost:16180/` | add the trailing slash on Reddit's side |
| `https://localhost:16180/` | `http://localhost:16180/` | change Reddit registration to `http://` |
| `http://127.0.0.1:16180/` | `http://localhost:16180/` | pass `--host 127.0.0.1` to reddi |

**"create app" button is missing entirely from /prefs/apps**

Reddit is hard-blocking app creation at the account level. Run through the pre-flight (verify email and phone), then:
- Try logging into <https://developers.reddit.com> once and accepting their terms there
- If still blocked, the account may be too new (Reddit sometimes gates accounts <30 days old or with <100 karma)
- Last resort: use a different Reddit account that meets the requirements, or wait for the gate to clear

**Devvit token appears (`npm create devvit@latest ...`)**

You're on the wrong platform — that's <https://developers.reddit.com> (Devvit, Reddit's *internal* app platform for apps that run inside Reddit). That doesn't help with reddi. Close that tab and go to <https://www.reddit.com/prefs/apps> instead (the classic OAuth surface). Different UI entirely; look for radio buttons (`web app` / `installed app` / `script`), not templates.

Enable shell tab-completion (optional, recommended):

```sh
# bash
eval "$(reddi completion bash)"

# zsh
eval "$(reddi completion zsh)"

# fish
reddi completion fish | source
```

After this, `reddi <TAB>` completes commands; `reddi auth <TAB>` completes subcommands.

## The launch workflow

This is what reddi is built for. The full loop in seven commands:

```sh
# 1. Find the right flair before posting
reddi flairs SideProject

# 2. Lint the post (dry-run, no submission)
reddi post --sub SideProject --title "I built reddi" --body-file post.md --dry-run

# 3. Submit it
reddi post --sub SideProject --title "I built reddi" --body-file post.md \
  --flair-id <id-from-step-1>

# 4. Watch it live, with a notification on removal
reddi watch <post-url> --interval 60 \
  --on-removal "osascript -e 'display notification \"reddi post removed\"'"

# 5. Stream inbox replies as they arrive
reddi inbox watch --mark-read

# 6. Reply to a specific comment
reddi comment <comment-url> --body "thanks for trying it!"

# 7. Crosspost to the next sub with a tailored title
reddi crosspost <post-url> --to MacApps \
  --title "[reddi] CLI for managing Reddit launches"
```

Or declare the whole thing as JSON and let reddi orchestrate:

```sh
reddi launch ~/launches/reddi/config.json
```

Where `config.json` is:

```json
{
  "name": "reddi v1.1 launch",
  "stages": [
    {"sub": "SideProject", "title": "I built reddi", "body_file": "post-sideproject.md"},
    {"sub": "MacApps",     "title": "[reddi] CLI for Reddit launches", "body_file": "post-macapps.md", "delay_seconds": 7200},
    {"sub": "ObsidianMD",  "title": "reddi: pipe Reddit ops through your vault", "body_file": "post-obsidian.md", "delay_seconds": 86400}
  ],
  "watch_after": true,
  "watch_duration_seconds": 86400,
  "watch_interval_seconds": 300,
  "on_removal": "osascript -e 'display notification \"reddi post removed\"'",
  "on_locked":  "tput bel"
}
```

## Full command reference

```text
reddi auth login           authenticate via browser OAuth
reddi auth status          show current auth state
reddi auth logout          remove stored credentials

reddi me                   show your account info
reddi history              list your own recent submissions

reddi post                 submit a text or link post (--dry-run supported)
reddi status <url>         vote/comment/removed-state for a post
reddi watch  <url>         live-updating dashboard
                           --on-removal / --on-locked fire shell hooks

reddi inbox list           list inbox items (--unread / --all)
reddi inbox watch          live-stream new items as they arrive
reddi inbox mark-read      mark items read (--id repeatable, or --all)

reddi comment <url>        post a top-level comment OR reply to a comment
reddi crosspost <url>      crosspost to another sub (--to)
reddi search <query>       search posts (--sub, --sort, --time, --limit)

reddi subs list            list your subscribed subs
reddi subs info <name>     subreddit metadata
reddi subs subscribe <name>     add subscription
reddi subs unsubscribe <name>   remove subscription

reddi flairs <sub>         list available flair templates for a sub
reddi launch <config>      multi-stage declarative launch orchestrator
reddi completion <shell>   emit bash/zsh/fish completion script

reddi devvit init          scaffold a Devvit project (Reddit's in-Reddit app platform)
reddi devvit dev           run the Devvit dev server
reddi devvit playtest <sub>  hot-reload to a real subreddit
reddi devvit upload        publish to Reddit
reddi devvit status        show Devvit project state
```

Every command takes `--json` for scripting.

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

# Watch a post during a launch with notifications on removal
reddi watch https://reddit.com/r/x/comments/abc/title/ \
  --on-removal "osascript -e 'display notification \"removed\"'"

# Stream inbox replies live with a terminal bell on each
reddi inbox watch --on-arrival "tput bel"

# Validate a launch config without submitting
reddi launch ~/launches/x/config.json --dry-run

# Find your removed posts
reddi history --json | jq '.[] | select(.removed) | .url'

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

## v1.x stability contract

The v1.0 surface is stable: flag shapes and JSON keys won't change incompatibly within the 1.x line. v1.1 adds new commands (`launch`, `history`, `completion`, `inbox watch`) and new flags on existing commands (`watch --on-removal`, `watch --on-locked`) — no breaking changes.

## Roadmap

- **v1.2** — `mod` commands for subreddit moderators (approve, remove, distinguish, lock, sticky)
- **v1.3** — TUI mode (`reddi tui`) for browsing
- **v2.0** — Possible Go rewrite for single-binary distribution via Homebrew

## Devvit companion (v1.2+)

Reddit has two separate developer surfaces, and reddi now manages both:

- **Classic OAuth API** (`/prefs/apps`) — what `reddi auth login` uses. External programs that talk to Reddit. The main reddi surface.
- **Devvit** (`developers.reddit.com`) — TypeScript/React apps that run *inside* Reddit (custom posts, mod tools). Distinct auth, distinct deployment.

`reddi devvit` wraps Reddit's Devvit CLI so both surfaces share one entry point. The Devvit project lives in a `devvit/` subfolder of your reddi checkout; the wrapper shells out to `npx devvit` and `npm` with the right cwd.

Quickstart for a Devvit companion app:

```sh
# In your reddi checkout (or any other dir — use --dir to override)
reddi devvit init                          # interactive; opens browser for auth
reddi devvit init --token <devvit-token>   # alternative: use a code from developers.reddit.com/new
reddi devvit status                        # confirm scaffolded
reddi devvit dev                           # run the dev server
reddi devvit playtest <your-test-sub>      # hot-reload to a real subreddit you mod
reddi devvit upload                        # publish to Reddit
```

The Devvit project is independent code (TypeScript/React) — reddi just orchestrates it. You can have *both* an installed-app OAuth credential (`reddi auth login`) for the classic API surface AND a Devvit app for in-Reddit features, managed from the same CLI.

## Related projects

- **[reddix](https://github.com/ck-zhang/reddix)** (~941★) — Reddit TUI for browsing. Different goal: replacing the browser as a reader. reddi targets posting/monitoring; reddix targets reading.
- **[rdt-cli](https://github.com/public-clis/rdt-cli)** (~366★) — terminal feed reader with light interaction.
- **[bdfr](https://github.com/Serene-Arc/bulk-downloader-for-reddit)** — bulk downloader for Reddit content (archival).
- **[PRAW](https://github.com/praw-dev/praw)** — the Python Reddit API Wrapper. reddi is built on top of it.

## Contributing

PRs welcome. Run tests with:

```sh
pip install -e ".[dev]"
ruff check reddi tests
pytest
```

CI runs ruff + pytest on Python 3.9 / 3.10 / 3.11 / 3.12.

## Why this exists in 2026

After Reddit's 2023 API pricing change killed Apollo, Reddit is Fun, BaconReader, `rtv`, and `tuir`, the Reddit-tooling ecosystem reset. The browsing-CLI niche has filled back in (reddix, rdt-cli, reddit-tui), but the *workflow* niche — for people who use Reddit to launch things — has stayed empty. PRAW is excellent as a library but doesn't give you a CLI; existing TUIs target reading, not posting. `reddi` fills that workflow gap.

## License

MIT — see `LICENSE`.
