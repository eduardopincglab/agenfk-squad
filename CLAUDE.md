# Squad: global agents (applies to every project)

Source: the `agenfk-squad` repository (linked into `~/.claude/` by `install.sh`). The project's own
`CLAUDE.md` / `AGENTS.md` and the AgenFK flow **take precedence over** this file.

## Who does what

| Request / flow step | Agent | Writes? |
|---|---|---|
| Start a feature or epic, prioritise, "how much is left", break down into cards | `product` | no (creates cards in TODO) |
| More than one agent or session in the same repo; branch/worktree per card; PR stack; "can I merge" | `github` | worktree claim only |
| IMPLEMENT / IN_PROGRESS: a card becomes code (backend, logic, API, data) | `developer` | yes, 1 card = 1 branch = 1 worktree |
| Screen, component, landing page, dashboard, design system, tokens, motion, Figma → code, art, poster, banner | `frontend` | yes, same regime |
| TEST: the card's tests, regression, coverage | `tester` (Sonnet) | test files only |
| REVIEW / ADVERSARIAL / MUTATE / VERIFY: before every PR | `verifier` (Sonnet) | no |
| An open PR a human must approve; "review PR 12", "what does this PR do" | `pull-request-reviewer` (DeepSeek flash via pi) | no, prints only |
| `infra/`, terraform, CI/CD, Dockerfile, cloud | `infra` | yes, stops at `plan` |
| Cloud cost, token cost, stack decision | `finops` | no |
| Pricing, margin, unit economics, portfolio | `finance` | no |
| Positioning, competitors, landing page (copy), outreach | `gtm` | no (drafts only) |
| Context > 60%, cockpit flashing HANDOFF, loop, "where did I stop", switching cards, closing the day | `context` (Sonnet) | handoff and card comment only |

## Dispatch rules

1. **Project specialist first.** If the project has its own agent for the
   role (`.claude/agents/`, e.g. a project-specific verifier such as
   `acme-verifier`, or `figma-implementer`), use it; the squad's agent is the
   default for when there is none.
2. **All code work goes through an AgenFK card.** Pass the card id to
   every agent that writes; it calls `agenfk gatekeeper --item-id <id>` before
   editing. No card: `product` (or `/agenfk`) creates one first.
3. **Parallelise by disjoint files, and `github` lays out the geometry.** Before
   dispatching two or more agents in the same repo, `github` delivers the map
   (session → worktree → branch → card), the table of fronts and the path of each
   worktree. One `developer`/`frontend` per card, in the same message, each
   in its own worktree. Ceiling ~4 fronts. Same file in two fronts = run them in series.
4. **Whoever writes does not approve.** REVIEW, ADVERSARIAL, MUTATE and VERIFY go to the
   `verifier` in a clean context: pass the card and the branch, not the
   implementer's narrative. FIX_FIRST/REJECT goes back to whoever implemented, at most 2
   rounds; after that it is the owner's decision.
5. **Only the main session advances a card** (`agenfk verify <id> --evidence ...`),
   with the evidence returned by the agents. No squad agent merges, runs
   `apply`, deploys, sends messages or publishes. Only `github` opens a PR, when the
   flow asks for it and the `verifier` returned SHIP. Once a PR is open, and only on a
   repository whose owner has agreed that its code may go to OpenRouter, dispatch
   `pull-request-reviewer` with its number and repository and relay the two sections
   it prints; posting the review stays a human decision.
6. **New cloud resource or stack choice** → `finops` quotes it before `infra`
   writes.
7. **Context is a budget, and the main session is the orchestrator that
   guards it.** The `squad-watch` hook measures every session and sub-session every minute and
   talks to you through `[squad-watch]` messages. They are orders, not suggestions:
   - **PROACTIVE HANDOFF** (the watcher's math, 1M window: context ≥ 80% of the
     window, or reread ≥ 60% with context above a floor that weighs the burn:
     50% of the window with burn ≥ 50% of the session budget, rising to 80% with
     zero burn; context at 50% with burn at 10% is not the time): close the step
     in progress, comment on the card, write the
     handoff through MODE A of `clear-pickup` **without asking for permission**, with what
     is left of the request under "Next step", and stop. When you stop, the watcher clears the
     session and calls the pickup by itself (herdr pane): the work continues in the
     new session. Stopping without writing the handoff brings the order back; stop again without
     it and the watcher writes a minimal handoff on its own (git, last
     request, denied dispatches) and switches the session anyway. Outside herdr,
     tell the owner `/clear` + `/clear-pickup pickup`. Do not open a new front.
     **The decision is the watcher's math, not your estimate:** do not write a handoff
     or stop "because the context is high" without a PROACTIVE HANDOFF, a DISPATCH
     DENIED or a request from the owner. An informational notice from the watcher is not an order to stop.
   - **Sub-session ended badly** (cut, loop, burn): do not redispatch the same
     brief. Read the return handoff, check in git what actually got done and
     dispatch only what is MISSING, with a short brief, in a new sub-session. 1 redispatch.
   - **DISPATCH DENIED** (orchestrator context ≥ 600k, 40 sub-sessions in the
     session, 3 sessions orchestrating at the same time, 7th reviewer on the same card):
     do not work around it with another tool or another agent type, and do not
     repeat the dispatch. The denial says where the work continues; do what
     it says:
     - *handoff with the plan* (context ceiling or sub-session ceiling; or no orchestrator
       slot with a heavy session, ≥ 120k): write the handoff with the
       plan of the denied dispatch under "Next step" (card, branch, worktree,
       files, steps, acceptance criteria, suite command) and stop. The
       watcher clears the session and the pickup executes the plan.
     - *do it right here* (no slot and a light session): implement the card in the
       main session, with no agent and no handoff. This is the authorised exception to the
       dispatch rule; the review still belongs to the `verifier`.
     - *no reviewer slot*: carry on with whatever does not depend on the verdict and dispatch
       when `SLOT FREE` arrives. Never approve your own code.
     - *7th reviewer*: comment on the card and take the decision to the owner.
     The stop is soft: only the new dispatch is denied, the task in progress finishes.
     Whoever orchestrates first receives a `DISPATCH NOTICE` (informational, not an
     order to stop), and the denied brief is kept in full in
     `~/.claude/squad/handoffs/<session>-dispatches.md`; point to it in the handoff.
   Sub-session brief: card, branch, worktree, files and next step; never
   the conversation. One card per sub-session; a card that does not fit in ~120k of context
   goes back to `product` to be split. One session per card per worktree.
   For the full picture: the `context` agent.
   - **MERGE QUEUE** (one per repository): landing on main happens one at a
     time. Before merging, request your turn: `squad-turn request <PR>` (the first
     `gh pr merge` also requests it). While another session holds the turn the merge is denied and
     you join the queue: **do not repeat the merge and do not sync with main
     while you wait**; main will move and the conflict you resolved will come back. Carry on with
     another step or stop, saying the PR is waiting for its turn. When `MERGE
     TURN` arrives: `git fetch`, `git merge origin/main` **once**, suite, push,
     merge. The watcher releases the turn when the PR shows up as MERGED; if you give up,
     `squad-turn release`. `squad-turn status` shows the queue, whether your branch
     conflicts with main and the files you have in common with whoever is ahead.
     Outside your turn, sync with main only when development needs
     something that has already landed (the watcher denies it once and explains; repeating goes through).
8. **Design in two layers, at most.** `frontend` loads
   `design-reference` + at most one design skill per task. Do not stack
   `frontend-design` + `ui-ux-pro-max` + `sumi:*`.
9. A task of 1–2 files with an obvious implementation: do it directly in the main
   session. An agent has a cost; do not dispatch what fits in a few calls.
