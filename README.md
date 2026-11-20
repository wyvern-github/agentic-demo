# agentic-demo

A GitHub Copilot workspace for building small Python office applications, desktop utilities, and mini games. New GUI projects default to PyQt6 and use SQLite only when they need relational storage.

## Start from a Brief

In VS Code, open a local Copilot Chat agent session and select **Python Developer**. Try either of these prompts:

- Build a PyQt invoice tracker with search and SQLite.
- Make a keyboard-controlled tile-matching mini game.

Developer calls **Python Planner** before coding, implements and tests each milestone, then calls **Python Reviewer** to review the result independently. You do not need to click handoff buttons. VS Code tool approvals still apply, and a missing reviewer is reported as pending, not passed. Select **Python Planner** or **Python Reviewer** directly for a standalone plan or review.

After planning, Developer shows the milestones and asks once when to commit, when to push, and whether to open a ready, draft, or no pull request. On a dedicated GitHub feature branch, committing and pushing each verified milestone gives you a visible history. You can also choose to push only at the end or keep the work local. To skip the questions, include choices in the brief, for example: `commit=milestone, push=end, pr=draft`. The PR is opened only after final tests and independent review pass and the verified head is pushed.

Each app task produces these root-level artifacts:

| File | Purpose |
| --- | --- |
| `PLAN.md` | Scope, design, acceptance criteria, and verification plan. |
| `MILESTONES.md` | Delivery checkpoints, test and review evidence, and Git delivery status. |
| `HANDOFF.md` | Chronological record of changes, checks, Git choices and results, blockers, and the next action. |
| `REVIEW.md` | Independent findings and verdict, with the branch, baseline, and known gaps. |

In a new session, select **Python Developer** and ask it to resume from `HANDOFF.md`. Use a separate workspace or branch for unrelated app experiments.

## Inspect the Setup

- **Agents:** [Python Planner](.github/agents/plan.agent.md), [Python Developer](.github/agents/developer.agent.md), [Python Reviewer](.github/agents/reviewer.agent.md).
- **Skills:** [PyQt UX/UI and color](.github/skills/pyqt-ux-ui/SKILL.md), [Advanced Python](.github/skills/advanced-python/SKILL.md), [SQLite management](.github/skills/sqlite-management/SKILL.md).
- **Instructions:** [Workspace workflow](.github/copilot-instructions.md), [Python](.github/instructions/python-standards.instructions.md), [pytest](.github/instructions/pytest.instructions.md), [PyQt interface](.github/instructions/pyqt-interface.instructions.md), [Review](.github/instructions/review.instructions.md), [Planning and handoff](.github/instructions/planning-workflow.instructions.md).

Run **Chat: Open Customizations** to check discovery. The agents request `reasoning-effort: max` when the selected model supports it; this is a reasoning preference, not a global creativity setting. The Markdown files guide agent behavior and do not bypass VS Code permissions.
