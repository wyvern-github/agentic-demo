---
description: "Use when planning, implementing, resuming, or handing off a Python app or mini game. Defines planning artifacts, Git milestone commits and pushes, and final GitHub pull requests."
---

# Planning and Handoff

## Before Writing Application Code

For every new application or planned feature, request a separate `PLAN.md` and `MILESTONES.md` from Python Planner and have it initialize `HANDOFF.md` in the workspace root. Do not ask the user to create these files. For planning-only requests, stop after writing the artifacts. For implementation, resolve the Git execution switches below once the milestones are clear, then proceed without routine confirmations.

- `PLAN.md`: Give the task a title and date. Capture the user's brief, assumptions, in-scope and out-of-scope work, numbered acceptance criteria, platform and dependency choices, UI/workflow or gameplay sketches in text, project structure, persistence needs, risks, and a verification strategy mapped to the acceptance criteria. State how to run and test the result. Add a Git Delivery section for the execution switches and any target details; mark unchosen values pending.
- `MILESTONES.md`: Use a table with milestone ID, deliverable and dependency, status, exit check, observed evidence, and Git delivery status. Use `Pending`, `In progress`, `Done`, or `Blocked` for the work, and track commit and push separately so a publication failure does not erase a passing exit check. Prefer independently testable slices. Include final testing and independent review as distinct gates. Do not mark a gate done without evidence.
- `HANDOFF.md`: Initialize with the task title, artifact paths, plan-ready state, and first action. Append chronological checkpoints with timestamp and time zone, role, milestone, changed paths, decisions, exact check commands and results, blockers, and the next executable action. Record the starting branch, commit (or unborn state), and pre-existing changes before implementation, then log Git delivery choices and outcomes as they happen. Never include secrets or sensitive data.

## Choose Git Execution Switches

The user-facing coordinator (Python Developer when selected directly, or the built-in Agent when it delegates) owns this checkpoint. After planning and before implementation, inspect the current Git branch, status, and configured remotes. Show a short milestone summary and suggest a cadence based on the number of milestones and whether the branch is shared. Ask for the missing switches together using the interactive questions tool when available, or ask in chat and wait. Treat explicit choices in the brief, or confirmed choices for the same task on resume, as answers; no need to ask again. An unanswered choice never authorizes a Git write or publication.

| Switch | Options | Recommendation |
| --- | --- | --- |
| `commit` | `milestone`: one commit per verified milestone with changes; `end`: one commit after final gates; `off`: no agent commits | Use `milestone` for independently testable slices; `end` can suit one small change. |
| `push` | `milestone`: push each milestone commit; `end`: push once after final gates; `off`: keep work local | Use `milestone` on a dedicated branch for visible progress; use `end` to publish a reviewed result only, or `off` without a suitable remote. |
| `pr` | `ready`: open a ready-for-review PR at the end; `draft`: open a draft at the end; `off`: no PR | Suggest `ready` for a completed feature branch, or `off` if there is no separate branch or no GitHub destination. |

Require a compatible combination: `push=milestone` needs `commit=milestone`; `commit=off` requires `push=off`; either PR mode requires a scheduled push and a named head branch distinct from the PR base. Identify the intended remote repository, remote head branch, and base for any PR. Confirm any ambiguous destination before editing Git state or publishing. Offer to create or switch to a feature branch if needed, but do so only with explicit authorization. Record the resolved switches and targets in `PLAN.md` and `HANDOFF.md`, and pass them to any implementation delegate. Agent tool approvals still apply.

## Commit and Push Verified Work

1. When a milestone's exit check passes, update `MILESTONES.md` and `HANDOFF.md` before staging. At the selected cadence, stage only in-scope product, tests, and task documentation. Inspect the complete staged diff and check for secrets, unrelated edits, generated output, and local data. If pre-existing staged changes or overlapping edits cannot be safely isolated, stop the Git action and report the blocker; do not unstage or commit the user's work. Skip empty commits.
2. Write a commit message that reads clearly on GitHub: `<milestone ID>: <imperative summary>`, then a short body headed `Scope`, `Why`, and `Verification` with the behavior delivered, rationale, and actual test commands and results. For an end-only commit, name the delivery and covering milestone IDs in the body. Include relevant issue references only when known.
3. Before pushing, verify the current branch and chosen destination and check the outgoing commit range for unintended commits. Push only the authorized branch to the approved remote; set an upstream only for the selected destination if needed. Never force-push, bypass hooks or branch protection, or push directly to a default or protected branch without explicit authorization. On authentication, approval, or non-fast-forward failure, keep local commits, log the blockage, and don't change the remote, branch, or history to work around it.
4. Record the actual commit SHA, push destination and result, or the reason for a skip or failure. Reconcile recorded state with Git before resuming; do not duplicate completed commits or pushes. Include delivery receipts in the next scheduled commit when relevant. Record final post-publish receipts locally and in the user-facing summary; do not create extra commits solely to record their own SHA or PR URL.

## Open the Final Pull Request

- Run final tests and obtain the independent review verdict before end-only Git actions and PR creation. Require both a passing final verification and `PASS` review for the final commit or push under an `end` switch and for any PR. Fix in-scope blocking findings and re-verify. On a blocked gate, leave earlier milestone commits and pushes intact and record what remains pending.
- If a PR was selected, confirm the verified final commit is pushed to the intended GitHub head and differs from the selected base. Use authenticated GitHub tooling such as `gh pr create` with an explicit repository, head and base, title, and body. Honor the selected ready/draft mode. Summarize scope and milestone commits, verification, the independent review, and known gaps. Reuse an existing open PR for the same repository, head and base; don't create a duplicate or change its status without authorization. Record the URL or the reason no PR was created. Do not merge it.

## During Implementation and Resume

- Read all three files and check the actual workspace before resuming. Use the most recent checkpoint as a starting point, not proof that the worktree still matches it. Reproduce the smallest relevant check if evidence is stale.
- Update the relevant milestone after each slice and append a checkpoint when work passes, is blocked, changes direction, or changes ownership. For changes to scope or acceptance criteria, record the reason in the plan and handoff instead of silently rewriting history.
- Keep unrelated active work intact. For a new task after a completed one, start a clearly labeled task section in the artifacts while preserving the previous record and making the current task unambiguous.
- At completion, record the launch command, full test result, independent report path and verdict or pending reason, commit and push results, PR URL or status, known gaps, and remaining work. Another agent must be able to resume without the original chat.
