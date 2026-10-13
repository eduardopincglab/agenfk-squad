---
name: pr-review
description: Run a read-only review of an open pull request on the newest DeepSeek flash through pi, and print what the PR does and its findings in the terminal. Wraps `scripts/pr_review.py` (`pr-review` on PATH after install.sh). Use when dispatching the `pull-request-reviewer` agent, when asked to "review PR 12 on DeepSeek", "pr-review", or to check which DeepSeek flash the reviewer uses.
---

# pr-review

`scripts/pr_review.py` runs one PR review in pi and prints it. The review
procedure itself belongs to the `pull-request` skill (`references/review.md`,
steps 1 to 5) and the prose rules to `house-style`; neither ships in this
repository. Install them in `~/.pi/agent/skills` or `~/.claude/skills`, or
point `PR_REVIEWER_SKILLS_DIR` at the directory that holds them.

## Requirements

| Needs | Check |
|---|---|
| pi, with the `openrouter` provider configured | `pi --list-models deepseek` lists `openrouter  deepseek/deepseek-v4.1-flash` |
| `gh`, logged in to the PR's repository (used by the script, never by the model) | `gh pr view <n> --repo <owner/name>` |
| The `pull-request` and `house-style` skills | `pr-review <n> --dry-run` exits 0 |

## Run

```bash
pr-review 12 --repo owner/name    # review and print
pr-review https://github.com/owner/name/pull/12
pr-review 12 --dry-run            # model and pi command only
```

The output starts with the PR, the model and any model notice, then the two
sections the reviewer must write: `## What this PR does` and `## Findings`
(verdict, then a severity table).

## Model

| Situation | Model used |
|---|---|
| `PR_REVIEWER_MODEL` set | That id, without reading the catalogue |
| The OpenRouter catalogue lists a flash newer than `PINNED` | The newest, with a notice to move the pin |
| The catalogue lists the pin as the newest flash | `PINNED` (`deepseek/deepseek-v4.1-flash`), no notice |
| The catalogue is unreachable, or lists no flash | `PINNED`, with a notice |

Only plain ids count as a flash: `deepseek/deepseek-vX.Y-flash`. Dated
snapshots, `:batch`, `-vision-exp` and the `~...-latest` aliases are ignored,
so a release is adopted when OpenRouter publishes its plain id.

## What the model can do

Nothing but answer. The script collects the PR first, with fixed `gh` reads
(`pr view`, `pr diff`, `pr checks`, `pr view --comments`, and `gh api` for each
changed file at the head commit, 60,000 characters per file and 600,000 in
all), runs the skill's `pr_check.py` and `inventory.py` on it, and attaches
the bundle to `pi -p --no-tools --no-extensions --no-skills --no-context-files`.
The review procedure and the house-style rules go in as system prompt text,
since the model has no tool to open them.

A PR is written by its author, and its body, comments or files can carry
instructions aimed at the model. Without tools the model has no shell to run
them in, and pi starts with an environment that keeps only `HOME`, `PATH`,
locale, proxy and CA variables and `OPENROUTER_API_KEY`: no `GH_TOKEN`, no AWS
profile, no SSH agent. Author text sits inside code fences longer than any
backtick run in it, and the prompt tells the model to report an embedded
instruction as a finding.

The bundle goes to OpenRouter and the model provider. Do not run it on code
that must not leave your organisation.

## Environment

| Variable | Default |
|---|---|
| `PR_REVIEWER_MODEL` | unset: newest flash |
| `PR_REVIEWER_SKILLS_DIR` | `~/.pi/agent/skills`, then `~/.claude/skills` |
| `PR_REVIEWER_CATALOG_URL` | `https://openrouter.ai/api/v1/models` |
| `PR_REVIEWER_TIMEOUT` | `900` seconds |

Exit codes: the review's own, `2` for a missing repository or skill, `124` for
a timeout, `127` when pi is not installed.
