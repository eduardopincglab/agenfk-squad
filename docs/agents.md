# Agent catalogue

Twelve agents, one file each in `agents/`. An agent is a Markdown prompt with
four frontmatter keys:

| Key | What it does |
|---|---|
| `name` | The id used to dispatch it. Equals the file name |
| `description` | When Claude Code should pick it. Written as trigger phrases |
| `tools` | The complete list of tools it may call. This is the hard limit |
| `model` | `inherit` (the model of the session that dispatches it) or a fixed one |

The **tool list is the enforcement**. A prompt that says "do not edit files"
is advice; an agent with no `Edit` and no `Write` cannot edit files. Read the
"Writes?" column below as a statement about tools, not about intentions.

## At a glance

| Agent | Flow step | Tools | Writes? | Model |
|---|---|---|---|---|
| [`product`](#product) | TODO | Read, Grep, Glob, Bash, WebFetch, WebSearch | No (creates cards through `agenfk`) | inherit |
| [`github`](#github) | before IMPLEMENT, at VERIFY | Read, Grep, Glob, Bash, Write | Worktree claims only | inherit |
| [`developer`](#developer) | IMPLEMENT | Read, Grep, Glob, Edit, Write, Bash | Yes | inherit |
| [`frontend`](#frontend) | IMPLEMENT | Read, Grep, Glob, Edit, Write, Bash, WebFetch, WebSearch | Yes | inherit |
| [`infra`](#infra) | IMPLEMENT | Read, Grep, Glob, Edit, Write, Bash | Yes, stops at `plan` | inherit |
| [`tester`](#tester) | TEST | Read, Grep, Glob, Edit, Write, Bash | Test files only | Sonnet |
| [`verifier`](#verifier) | REVIEW, ADVERSARIAL, MUTATE, VERIFY | Read, Grep, Glob, Bash | No | Sonnet |
| [`pull-request-reviewer`](#pull-request-reviewer) | after a PR is opened | Bash, Read | No (prints only) | Haiku; the review runs on DeepSeek flash |
| [`finops`](#finops) | before a stack or cloud decision | Read, Grep, Glob, Bash, WebFetch, WebSearch | No | inherit |
| [`finance`](#finance) | on request | Read, Grep, Glob, Bash, WebFetch, WebSearch | No | inherit |
| [`gtm`](#gtm) | on request | Read, Grep, Glob, Bash, WebFetch, WebSearch | No (drafts only) | inherit |
| [`context`](#context) | any time | Read, Grep, Glob, Bash, Write | Handoffs and card comments only | Sonnet |

Two notes on that table.

- Several read-only agents have `Bash`. A shell can write. For those agents
  the limit on writing is a rule in the prompt, and it is weaker than a
  missing tool. Tightening this with per-agent permission rules is on the
  [roadmap](../ROADMAP.md).
- `tester`, `verifier` and `context` run on Sonnet on purpose. Their work is
  mechanical and high-volume (run the suite, mutate, measure), a cheaper model
  does it well, and a reviewer on a different model than the author shares
  fewer of its blind spots.

## Rules that apply to every agent

From `CLAUDE.md`, and repeated in each agent file where they bind:

1. **The project's own specialist comes first.** If the project defines an
   agent for the same role in `.claude/agents/`, that one is used.
2. **No card, no code.** An agent that writes receives the card id and calls
   `agenfk gatekeeper --item-id <id>` before the first edit.
3. **No agent advances a card.** Only the main session runs `agenfk verify`.
4. **No agent merges, applies, deploys, sends a message or publishes.**
5. **A brief is a card, a branch, a worktree, files and a next step.** Never
   the conversation.
6. **Project instructions win.** Every agent reads the project's `CLAUDE.md`
   or `AGENTS.md` before acting.

## product

**Says where the project really is, and cuts the work.**

Reads the repository and the board, not the plan on paper. Measures the
distance to a real user, cuts the goal to the smallest increment that someone
can use, and breaks it into AgenFK cards with scope, acceptance criteria and
dependencies.

- **Dispatch when:** starting a feature or epic; choosing the next block;
  planning the week; "how much is left", "what's next", "can we go faster".
- **Returns:** the real state, the cards created (in TODO), what was cut and why.
- **Never:** edits code, estimates without reading the repository, creates a
  card whose acceptance cannot be checked by running something.

## github

**Controls branches, worktrees, PRs and parallelism.**

Maps who is where (Claude Code, Codex and pi sessions; AgenFK cards; open
PRs), plans parallel fronts over disjoint files, opens the branch and worktree
for each card, records the writer of each worktree, keeps the PR stack
readable, proposes the merge train, and cleans up what died.

- **Dispatch when:** before sending more than one agent or session into the
  same repository; starting a new card; two sessions collide; the PR stack or
  CI is confusing; closing the day; "what is open", "can I merge".
- **Returns:** the map (session → worktree → branch → card → PR), the table of
  fronts, the path of each worktree, the proposed merge order.
- **Never:** merges, force-pushes, applies or deploys. It opens a PR only when
  the flow asks for one and the `verifier` returned `SHIP`.
- **Uses:** the `parallel-git` skill.

## developer

**Turns exactly one card into code.**

One card, one branch, one worktree, with the project's suite as the gate.

- **Dispatch when:** a card with clear scope and acceptance criteria needs to
  become code. In parallel, one agent per card, when the cards touch disjoint
  files.
- **Returns:** files changed, a summary, risks, what was deferred, and the
  suite result as it ran.
- **Never:** opens a PR, merges, or touches infrastructure, CI, migrations or
  dependencies. Those belong to `infra` or need the owner.

## frontend

**Design director and design engineer.**

Creates, rebuilds and audits interfaces (web, mobile, desktop, dashboards,
landing pages, components, design systems, tokens, dark mode, motion) and
produces visual pieces (posters, banners, icons, slides, generative art). It
decides a direction before writing code and holds the result to a measured
quality floor.

- **Dispatch when:** a card changes how something looks, is used, moves or is
  touched; implementing a design from Figma; auditing or repairing
  AI-generated UI; defining a design system.
- **Returns:** the direction taken and why, files changed, the quality-floor
  checklist with what was measured.
- **Never:** opens a PR or merges. Loads the `design-reference` skill plus
  **at most one** other design skill per task.

## infra

**Infrastructure, CI/CD and operations. Stops at `plan`.**

Writes and validates Terraform and pipelines, and reviews an infrastructure
design before it becomes code: cost, IAM, network, persistence, rollback.

- **Dispatch when:** a card needs a cloud resource, or touches `infra/`,
  Terraform, CI workflows, Dockerfiles or environment migrations; CI is broken.
- **Returns:** the plan output, findings tagged `[CRITICAL]`, `[WARNING]` or
  `[SUGGESTION]`, and what the owner must run.
- **Never:** `apply`, `destroy` or deploy. A new cloud resource is priced by
  `finops` **before** `infra` writes it.

## tester

**Writes the card's tests and proves each one can fail.**

Happy path, edges and failures. For every new test it mutates the production
code the test targets, watches the test go red, and restores the code. A
defect found by running the system becomes a regression test.

- **Dispatch when:** after every implementation; a defect needs a regression
  test; coverage needs to rise.
- **Returns:** the tests added, the suite result, and for each test the
  mutation that made it fail. Logged on the card.
- **Never:** edits anything but test files. If the code is wrong, it reports;
  it does not fix.

## verifier

**Independent reviewer, read-only, in a clean context.**

Judges a card's branch against its acceptance criteria. Runs the suite itself,
mutates production code to prove the tests fail, hunts for regressions, broken
integration and security flaws.

- **Dispatch when:** REVIEW, ADVERSARIAL, MUTATE and VERIFY of any flow;
  before every PR; whenever the one asking for approval is the one who wrote
  the code.
- **Brief with:** the card id and the branch. **Not** the implementer's
  account of the work.
- **Returns:** `SHIP`, `FIX_FIRST` or `REJECT`, with blockers, warnings, the
  suite as reproduced, mutation results and integration results.
- **Never:** fixes what it finds. It has no `Edit` and no `Write`.
- **Cap:** two `FIX_FIRST`/`REJECT` rounds per card; the watcher denies a
  seventh reviewer dispatch on the same card.

## pull-request-reviewer

**Prints what an open PR does, and what is wrong with it, for the people who approve it.**

A Claude Code sub-agent can only run Claude models, so this one is a Haiku
dispatcher around `pr-review` (`skills/pr-review`). That script runs the review
in pi on the newest DeepSeek flash in the OpenRouter catalogue, pinned to
`deepseek/deepseek-v4.1-flash` and announcing a newer one when it uses it. The
review follows the `pull-request` skill's procedure and the `house-style`
rules, which you install separately.

- **Dispatch when:** a PR was just opened in a long orchestration; a human has
  to approve a PR someone else wrote; "review PR 12", "what does this PR do".
- **Brief with:** the PR number or URL and the repository.
- **Returns:** the model used, `What this PR does`, and `Findings` (verdict and
  a severity table), as printed by `pr-review`, plus its exit code.
- **Never:** posts, approves, comments, edits, merges, commits or pushes. The
  script collects the PR with `gh` reads and runs pi with no tools and without
  GitHub or cloud credentials in its environment, so instructions hidden in a
  PR have no tool to act through in pi. The Haiku dispatcher that relays the
  output does have Bash, and treats the output as data. The PR's code goes to OpenRouter: do not
  dispatch it on code that must not leave your organisation.
- **Not the verifier:** the `verifier` judges a card's branch before the PR,
  with the suite and mutation. This agent reads the PR once it exists.

## finops

**The cost of engineering.**

Prices the monthly cloud cost of a design line by line, each line with a
source, a date and a formula, at the measured volume and at ten times it.
Measures token spend per card, project and model from AgenFK.

- **Dispatch when:** before any stack decision or new cloud resource; a
  document needs a cost table; closing an epic; "how much does this cost",
  "where can we cut".
- **Never:** quotes a price without a dated source, or presents an assumption
  as a measurement.

## finance

**Product finance.**

Unit economics, pricing, margin, break-even and runway, for a project or for
the portfolio. Cloud and token cost come from `finops`; this agent joins cost
with revenue.

- **Dispatch when:** pricing, a paid plan, margin per customer or operation,
  the viability of a feature with a variable cost, comparing projects by return.
- **Never:** computes from data it does not have. Without the data it returns
  the list of what is missing.

## gtm

**Go-to-market, drafts only.**

Positioning, ideal customer, competitor analysis, value proposition, landing
and pricing page copy, outreach and demo scripts, a list of channels.

- **Dispatch when:** "how do we sell this", "who is it for", "landing page",
  "pitch", "competitors", "first customers"; preparing a launch.
- **Never:** sends a message, publishes, contacts a person or creates an
  account. Everything it produces is a draft for the owner to use.

## context

**Manages the context of the sessions themselves.**

Measures context, weighted burn, reread share, waste, loops and the age of the
last handoff for each live session. Decides between continue, compact, hand
off, cut a loop or close, and runs the switch between tasks: pause the card,
write the handoff from ground truth, open a new session per card and
worktree, verify the pickup.

- **Dispatch when:** context passes 60%; a session feels repetitive or slow;
  before `/compact` or `/clear`; switching cards; opening several sessions;
  closing the day; "how much am I spending", "is it looping", "where did I stop".
- **Never:** writes to a transcript, or edits anything but handoffs and card
  comments.
- **Uses:** the `session-context` and `clear-pickup` skills.

The watcher covers the automatic cases without this agent. The agent is for
the full picture: every session on the machine, and a recommendation for each.

## Adding or replacing an agent

To change an agent **for one project**, put a file with the same `name` in
that project's `.claude/agents/`. It replaces the squad's agent there.

To propose an agent **for the squad**, see
[CONTRIBUTING.md](../CONTRIBUTING.md#proposing-an-agent). The bar is
deliberate: a role enters after it has been needed in two projects, and one
that has not been dispatched in thirty days is a candidate for removal.
Every agent's description competes with all the others for the model's
attention, so each addition makes the rest slightly harder to pick correctly.
