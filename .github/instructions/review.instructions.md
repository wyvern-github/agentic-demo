---
description: "Use when independently reviewing a Python application or mini game, checking the active Git branch or changes since the last review, or writing the REVIEW.md report."
---

# Independent Review and Report

## Identify the State Under Review

1. Read the brief, acceptance criteria, test evidence, and any previous `REVIEW.md`. Record the current branch or detached state, `HEAD` or unborn state, and staged, unstaged, and relevant untracked paths. Use read-only Git inspection. Don't fetch, switch branches, stage, commit, or run repository code to obtain the review scope.
2. Select a baseline in order: an explicit user-supplied ref, the last exact reviewed commit if verifiable on the current history, the merge base with an available local GitHub target or configured upstream ref, then the starting `HEAD` from `HANDOFF.md` or current `HEAD`. Name the chosen ref and SHA and explain any fallback. On an unborn branch, inspect the current project without claiming a commit comparison.
3. Use commit history and the baseline diff to see committed changes; inspect staged, unstaged, and relevant untracked product files too. Don't mistake the tracked diff for the whole working tree. Identify known pre-existing changes separately. If the previous review included uncommitted content that cannot be reconstructed, disclose that and review the current cumulative diff instead of claiming an exact delta.

## Examine the Solution

- Check the entire solution against the plan, not just changed lines: app entry point, main flows, data handling, failure recovery, tests, dependencies, and run documentation. In a follow-up, pair changed areas with their callers and tests and verify prior blocking findings. State exactly what was reviewed.
- Prioritize correctness, data loss, regressions, insecure or unsafe defaults, and missing evidence for critical behavior. For PyQt, include resize, keyboard and accessibility, responsiveness, and meaningful feedback. For SQLite, include constraints, migration and save failure safety, and reopening persisted data. For games, include state transitions and pause/restart. Use the relevant domain guides.
- Cite reproducible evidence, not style preference. Read the tests and compare the reported runs to the reviewed state. Separate observations from inferences; don't claim tests or manual checks you did not run.

## Write `REVIEW.md`

- Start with findings ordered by severity (`P0` critical, `P1` high, `P2` medium, `P3` low). For each, include a title, file and line, affected scenario, impact, and an actionable correction or test. If none, say so explicitly.
- Add verdict (`PASS`, `CHANGES REQUIRED`, or `BLOCKED`), date, scope, branch, `HEAD`, baseline and rationale, dirty or clean product state, acceptance coverage, checks and their source, and remaining gaps. Use `CHANGES REQUIRED` for blocking findings and `BLOCKED` when essential evidence is unavailable. Use `PASS` only when no blockers remain and the required evidence is available.
- Record a reusable exact reviewed commit only if the reviewed product content matches it. Otherwise label the commit as the review's `HEAD`, not an exact snapshot. In a re-review, note the previous verdict and which findings were resolved, remain open, or are new.
