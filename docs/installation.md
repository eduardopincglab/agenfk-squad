# Installation

The squad installs at the **user level** of Claude Code: it applies to every
project you open. Read this page once before running the installer, because
one of the things it links is your global `CLAUDE.md`.

## Requirements

| Needed | Why |
|---|---|
| [Claude Code](https://claude.com/claude-code) | The harness the agents and hooks run in |
| Python 3.10 or newer, as `python3` | The hooks and the session report. Standard library only |
| `git` | Worktrees, the merge queue, the handoff's ground truth |
| [AgenFK](https://github.com/cglab-public/agenfk) | Cards, flow and gates. The agents call its CLI |
| Linux or macOS | The hooks use POSIX file locking. Developed and run daily on Linux; macOS is untested |

### Optional dependencies

| Optional | What you get | Without it |
|---|---|---|
| **herdr** (a terminal pane manager for agent sessions) | The automatic session switch, and `MERGE TURN` delivered as a prompt into the waiting pane | The watcher still orders the handoff; you type `/clear` and `/clear-pickup pickup`. A queued session sees `MERGE TURN` on its next prompt |
| **GitHub CLI** (`gh`), logged in | The merge queue releases the turn as soon as the PR shows MERGED or CLOSED | The turn is released by `squad-turn release` or by timeout |
| A status line that writes `~/.claude/cache/session-tokens/<session>.json` with a `window` field | The watcher learns a window larger than 1M | Set `SQUAD_WINDOW` yourself |

## Install

```bash
git clone https://github.com/eduardopin/agenfk-squad.git
cd agenfk-squad
./install.sh
```

Keep the clone. The installer creates **symlinks** into it, so the directory
has to stay where it is, and `git pull` is how you update.

### What the installer does

It links, into `${CLAUDE_CONFIG_DIR:-~/.claude}`:

| Link | Target |
|---|---|
| `agents/<name>.md` | each file in `agents/` |
| `skills/<name>` | each skill directory that has a `SKILL.md`, including those in `skills/vendor/` |
| `CLAUDE.md` | `CLAUDE.md` |
| `hooks/squad-router.py`, `squad-watch.py`, `squad-switch.py`, `squad-turn.py` | the four files in `hooks/` |

and, so that the merge queue can be called by name:

| Link | Target |
|---|---|
| `~/.local/bin/squad-turn` | `hooks/squad-turn.py` |
| `~/.local/bin/pr-review` | `skills/pr-review/scripts/pr_review.py` |

Make sure `~/.local/bin` is on your `PATH`.

### What it will not do

- **It never overwrites a real file.** If the destination exists and is not a
  symlink, it prints `SKIPPED`, leaves the file alone, and exits non-zero at
  the end so you notice.
- **It does not edit `settings.json`.** Registering the hooks is the next
  step, by hand.
- **It does not install AgenFK.** It warns if `agenfk` is not on your PATH.

It is idempotent: running it again refreshes the links.

### If you already have a `~/.claude/CLAUDE.md`

The installer skips it. You then have two options:

- **Merge by hand.** Copy the sections of this repository's `CLAUDE.md` into
  yours. You lose automatic updates of that file.
- **Import.** Keep your file and add a line that pulls the squad's rules in:

  ```markdown
  @/absolute/path/to/agenfk-squad/CLAUDE.md
  ```

The same applies to an agent or skill of yours with a clashing name: rename
yours, or leave the squad's one unlinked.

## Register the hooks

Add this to `~/.claude/settings.json`, merging with any `hooks` you already
have. Replace `~/.claude` with the absolute path if your shell does not expand
`~` inside the command.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-router.py", "timeout": 5 },
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-watch.py", "timeout": 10 }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-watch.py", "timeout": 10 }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-watch.py", "timeout": 10 }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-watch.py", "timeout": 10 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/squad-watch.py", "timeout": 10 }
        ]
      }
    ]
  }
}
```

| Script | Events |
|---|---|
| `squad-router.py` | `UserPromptSubmit` |
| `squad-watch.py` | `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `SubagentStop`, `Stop` |

`squad-switch.py` and `squad-turn.py` are not registered: the watcher starts
them when needed.

You can adopt the squad in stages. The agents and skills work without any
hook. The router works without the watcher. The watcher works without herdr.

## Check it

Start a **new** Claude Code session (agents, skills and hooks are read at
session start) and:

```bash
# the report runs and lists your sessions
python3 skills/session-context/scripts/session_context.py

# the queue answers, from inside any git repository
squad-turn status

# the suite passes
python3 tests/test_watch.py
```

In the session, `/agents` should list the twelve squad agents, and a prompt
such as `how much is left on this epic?` should come back with a
`[squad route]` hint.

Then set up AgenFK for your project and activate the flow:
[agenfk-integration.md](agenfk-integration.md#setting-it-up).

## Update

```bash
cd agenfk-squad
git pull
./install.sh      # only needed when files were added or renamed
```

## Uninstall

Remove the hook entries from `settings.json`, then remove the links. This
deletes only symlinks that point into your clone:

```bash
SQUAD="$(pwd)"    # run from the agenfk-squad clone
find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "$HOME/.local/bin" -maxdepth 2 -type l \
  -lname "$SQUAD/*" -print -delete
```

State under `~/.claude/squad/` is plain files; delete the directory if you
want it gone.

## Turning parts off without uninstalling

```bash
export SQUAD_WATCH=0     # the whole watcher
export SQUAD_SWITCH=0    # only the automatic session switch
export SQUAD_TURN=0      # only the merge queue
```

All variables: [configuration.md](configuration.md).

## A note on "the cockpit"

Some files mention a *cockpit*. It is the author's Claude Code status line,
which shows the same numbers the watcher computes (context, burn, reread
share) and records each session's real window. It is not part of this
repository and nothing here needs it: the watcher reads the transcripts
itself.

## Troubleshooting

| Symptom | Look at |
|---|---|
| No `[squad-watch]` messages at all | Is the hook registered for the event? Is `SQUAD_WATCH=0` set? `~/.claude/squad/watch-errors.log` |
| The handoff was ordered but the session did not switch | `~/.claude/squad/switches.log` says which check gave up. Outside herdr, this is expected |
| `squad-turn: command not found` | `~/.local/bin` is not on your `PATH` |
| A merge is denied and nobody seems to hold the turn | `squad-turn status`. A stale turn clears by itself after `SQUAD_TURN_IDLE` seconds |
| The handoff comes too early or too late | `session_context.py --session <id> --detail` shows the numbers the watcher used. Then [configuration.md](configuration.md#choosing-your-own-numbers) |
| An agent is not picked for a request | A project agent with the same role wins. Otherwise check the `description` in `agents/<name>.md` |
