# Contributing

Thank you for looking. This project is one person's working setup, published
so that others can test the idea against their own sessions. The sample behind
every rule here is one machine. Yours is the second data point.

## What helps most

In order of value:

1. **A failure you observed, with numbers.** A session cut too early. A loop
   the watcher missed. A denial the model worked around. A merge queue that
   stalled. Open an issue with what `session_context.py --detail` showed and
   the `[squad-watch]` message as printed.
2. **Your thresholds.** If your data says the defaults are wrong for a 200k
   window, or for a team, say so and show the data.
3. **Another harness.** The agents are plain Markdown and travel well. The
   hooks speak Claude Code's hook protocol and do not travel at all yet.
4. **A rule, an agent or a skill**, following the bars below.
5. **Documentation.** If a page left you guessing, that is a bug.

## Ground rules

- **Evidence before design.** A proposal starts with the failure it answers.
  "It would be nice if" is not a failure.
- **Every refusal names a way forward.** A new denial that only says no will
  not be merged. Say where the work continues.
- **Every hook change ships with a test that fails without it.**
- **The watcher does not change behaviour silently.** A changed threshold,
  keyword or state path is a breaking change: `CLAUDE.md`, the agents and the
  tests all match on those strings.
- **Standard library only** in `hooks/` and `skills/*/scripts/`.
- **No private context.** No absolute home paths, no real project or customer
  names, no session ids, no transcripts.
- **English** for everything a reader sees. The two bilingual regexes
  (the router's patterns, and `ASKED_TO_STOP` / `RESUME` in the watcher) read
  what an owner types, and owners write in any language: adding a language
  there is welcome. Keep router patterns specific: the English alternatives
  are broader than the Portuguese originals were (`page`, `component`,
  `priority`), and a pattern that fires on every prompt is noise. Narrowing
  one, with the prompts that misrouted, is a good first contribution.

## Setting up

```bash
git clone https://github.com/eduardopin/agenfk-squad.git
cd agenfk-squad
python3 tests/test_watch.py
```

You do **not** need to run `install.sh` to work on the repository, and you
should not run it from a development clone unless you want your own Claude
Code sessions to use your work in progress. The hooks run on every tool call
of every session on your machine: a syntax error in `squad-watch.py` fails
open (it is silent), but a wrong rule will deny real work.

To try a change safely, point a throwaway config at your clone:

```bash
CLAUDE_CONFIG_DIR=/tmp/claude-test HOME=/tmp/claude-test-home ./install.sh
```

## Running the checks

```bash
python3 tests/test_watch.py
python3 tests/test_pr_review.py
python3 -m py_compile hooks/*.py skills/*/scripts/*.py
bash -n install.sh
```

The suite has no dependencies and no test runner. Each test builds a fake
transcript and a temporary state directory, feeds hook payloads to the real
scripts as subprocesses, and asserts on what they print. It prints `ok` per
test and exits non-zero on the first failure. CI runs the same three commands, plus a grep for private home paths,
on Python 3.10, 3.12 and 3.14.

## Proposing a watcher rule

1. Open a **Proposal** issue: the failure, the numbers, the rule, and what the
   session is told to do next.
2. Write the test first. It should build the situation (a transcript with the
   right token usage, a state file, a payload) and assert on the keyword and on
   the exit named in the message.
3. Implement the rule in `hooks/squad-watch.py`. Keep the hot path cheap: the
   hook runs before and after every tool call.
4. Put any new threshold behind an environment variable with a default, read
   through `env_int` so that a bad value falls back, and document it in
   `docs/configuration.md` and in the script's header.
5. If the session has to act on a new keyword, teach it in `CLAUDE.md`, in the
   same pull request.
6. Describe the rule in `docs/watcher.md`.

## Proposing an agent

The house rule: **a role enters after it has shown up in two projects, and an
agent that has not been dispatched in thirty days is a candidate to leave.**
Each agent's description competes with every other for the model's attention.

A new agent needs:

- A **role no existing agent has.** If it overlaps, propose a change to that
  agent instead.
- The **smallest tool list** that does the job. Read-only by default. If it
  must write, say exactly what.
- A **description made of trigger phrases** a user would actually type.
- **Explicit limits**: what it never does, and what it hands to which other agent.
- A **return format**: what it gives back to the main session, as evidence.
- A row in `CLAUDE.md` ("Who does what"), in `README.md` and in `docs/agents.md`.
- If it maps to a flow step, a line in `flows/squad-delivery.json` and
  `docs/agenfk-integration.md`.

## Proposing a skill

A skill is a procedure an agent loads on demand: `skills/<name>/SKILL.md`,
with `name` (equal to the directory) and `description` in the frontmatter.

- Keep it to a procedure with steps that can be checked. Background reading
  belongs in `references/` inside the skill, loaded only when needed.
- Scripts go in `scripts/`, standard library only, with `--help`.
- Third-party skills go under `skills/vendor/`, unmodified, with their
  license file, and are listed in `NOTICE`.

## Improving an agent prompt

Prompt changes are the hardest to review, because a diff does not show
behaviour. In the pull request, include:

- the situation in which the agent did the wrong thing;
- what it did, and what it should have done;
- the change, as small as it can be.

Avoid adding emphasis ("IMPORTANT", "NEVER" in capitals) to fix one case. It
makes the agent rigid everywhere else. Explain the reason for the rule instead.

## Pull requests

- One change per pull request. Small ones are reviewed quickly.
- Fill in the template. The checklist is the review.
- Commit messages in the imperative, with the reason in the body when it is
  not obvious.
- By contributing you agree that your contribution is licensed under the
  [ISC License](LICENSE).

## Where things are

| You want to change | Look at |
|---|---|
| Who gets dispatched for what | `CLAUDE.md`, `hooks/squad-router.py` |
| What an agent may do | `agents/<name>.md` |
| When a session is told to hand off | `handoff_math` in `skills/session-context/scripts/session_context.py` |
| What happens at each hook event | `hooks/squad-watch.py` (`pre_tool`, `post_tool`, `subagent_stop`, `stop`) |
| The dispatch brake | `pre_dispatch` in `hooks/squad-watch.py` |
| The merge queue | the `turn_*` functions in `hooks/squad-watch.py`, `hooks/squad-turn.py` |
| The session switch | `hooks/squad-switch.py` |
| The handoff file format | `skills/clear-pickup/SKILL.md` |
| The flow | `flows/squad-delivery.json` |

## Questions

Open an issue. For anything about AgenFK itself (the CLI, the board, flows,
gates), the place is <https://github.com/cglab-public/agenfk>.

Please read the [Code of Conduct](CODE_OF_CONDUCT.md). Security reports:
[SECURITY.md](SECURITY.md).
