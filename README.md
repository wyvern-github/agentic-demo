# agentic-demo: customization experiments

These branches compare repository-level Copilot customizations for small Python desktop apps and games. Each experiment starts from the same `main` commit:

| Branch | Custom agents | Instructions | Skills |
| --- | --- | --- | --- |
| `main` | Yes | Yes | Yes |
| `experiment/no-agents` | No | Yes | Yes |
| `experiment/no-instructions` | Yes | No | Yes |
| `experiment/no-skills` | Yes | Yes | No |
| `experiment/only-instructions` | No | Yes | No |
| `experiment/only-skills` | No | No | Yes |

Instructions include both `.github/copilot-instructions.md` and `.github/instructions/`. Remaining files have been adjusted to avoid references to removed customizations, so this is not a perfectly isolated single-variable experiment.

## Run a comparison

1. Check out one experiment branch in a clean workspace, before making any test changes. Start a new Copilot Chat session using the same model, settings, and built-in Agent mode for every branch.
2. Use **Chat: Open Customizations** to check what is discovered. Disable or account for user-level, organization-level, plugin, and other external customizations: these branches only control the repository's files. Built-in agents and tools may still be available.
3. Give the same prompt and Git delivery choices in every session. Commit the resulting work to that experiment branch, and record the prompt, environment, approvals, and results for comparison. Start each other experiment from its own unchanged branch, not from a prior experiment's result.

The experiment branches are local unless explicitly pushed. Switch branches or use separate worktrees only after saving any work you want to keep. Copilot customization files guide behavior; they do not bypass tool permissions.
