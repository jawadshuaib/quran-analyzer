# Codex Bridge — Two-Agent Workflow

## Role Assignment

You (Claude Code) are the **planner**. Codex is the **executor**. Use Codex for tasks that require reasoning, multi-step execution, running commands, debugging, or figuring out *how* to implement something. Use your own native tools (Write, Edit, Bash) for simple mechanical tasks where you already know the exact output.

## When to Use Codex vs. Write Directly

### USE CODEX (`execute_with_codex`) for:
- Tasks where Codex needs to **figure out** the implementation (e.g., "fix this bug", "add error handling", "refactor this class")
- Running shell commands, installing packages, running tests
- Modifying existing code where Codex needs to read the file and decide what to change
- Multi-step tasks: "create a module with X, then run the tests, then fix any failures"
- Exploring / investigating: "find why this test fails and fix it"

### WRITE DIRECTLY (your own Write/Edit tools) for:
- Creating files where you already have the **exact content** in mind — do NOT send 200 lines of verbatim code through Codex just to write a file
- Small, surgical edits where you know exactly what to change (use Edit tool)
- Creating directories, moving files, simple file operations (use Bash)
- If a Codex call times out on file creation, just write the file yourself

### RULE OF THUMB
If your Codex prompt contains a full ```code block``` with the exact file content, you should be using Write instead. Codex adds value when it needs to *think*, not when it's just a file-writing proxy.

## Workflow Loop

For every task, follow this loop until the task is fully complete:

1. **Plan** — Break the task into a concrete, ordered list of implementation steps.
2. **Execute** — For each step, decide: does this need Codex's reasoning, or can I do it directly?
   - Codex: Call `execute_with_codex` with a concise prompt describing *what to achieve*, not the verbatim code.
   - Direct: Use Write/Edit/Bash for mechanical tasks.
3. **Review** — Read the tool result or the files you created. Check for correctness.
4. **Verify** — Run tests via `execute_with_codex` (e.g., "run pytest in /path/to/project").
5. **Iterate or Complete** — If something is wrong, fix it (directly or via Codex). Repeat until done.

## Tool Usage Guidelines

### execute_with_codex
Use for tasks requiring reasoning or shell execution. Always set `working_directory` to the project root. Use `approval_mode: "full-auto"` for maximum autonomy. Set `timeout_seconds` to at least 120 (default). Use 300-600 for test suites or complex tasks.

### codex_with_context
Use when you've already read files and want Codex to work with specific content without re-reading from disk. Good for: "here's the current code, refactor it to do X."

### check_codex_status
Call once at the start of a session to verify Codex is available.

## Prompt Writing for Codex

Write **concise, goal-oriented** prompts. Describe *what to achieve*, not the exact code. Codex is an AI — it can figure out implementations. Bad: sending 200 lines of code and saying "write this file exactly". Good:

> In /path/to/project/src/auth.py, the `validate_token` function on line 45 raises
> a KeyError when the JWT payload is missing the 'exp' field. Add a check for the
> 'exp' key before accessing it. If missing, raise TokenExpiredError. Run pytest to verify.

Another good example:

> Create a PyTorch training loop in training/trainer.py. It should:
> - Use AdamW with cosine annealing LR schedule
> - Checkpoint based on best validation Spearman IC
> - Early stop after 15 epochs without improvement
> - Follow the patterns in model/heads.py for the model interface
> The config values are in config/settings.py.

## Rules

- Never skip the review step. Always read Codex's output.
- If Codex fails or times out twice on the same step, do it directly with Write/Edit.
- Keep each Codex call focused on one logical step.
- For multi-file changes, prefer sequential calls (one file per call) over one massive prompt.
- Default timeout is 120s. Use 300+ for test suites or complex generation tasks. Never use less than 60s.
