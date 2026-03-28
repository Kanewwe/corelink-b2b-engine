---
description: Linkora v3.0+ Standard Development Workflow (Verification & Deployment)
---

To ensure high-quality delivery and efficient progress, follow these steps for every task:

0. **Plan & Review [NEW]**:
   - Create or update an `implementation_plan.md` for any non-trivial task.
   - Wait for explicit user approval before starting code implementation.

1. **Local Implementation**:
   - Apply code changes to the relevant backend or frontend files.
   - For frontend changes, always check for unused variables or missing imports.

2. **Local Verification [CRITICAL]**:
   // turbo
   - Run `npm run build` (or `tsc`) in the `frontend` directory to catch lint/type errors.
   - Run existing Python tests if backend logic is modified.
   - Use the `browser_subagent` tool to verify UI changes if possible.

3. **Code Review & Walkthrough [NEW]**:
   - After implementation, summarize changes in `walkthrough.md`.
   - Ensure the user has visibility into the exact diffs and rationale.

3. **Incremental Commits**:
   - Once a sub-task is verified locally, stage the files.
   - Commit with a clear, concise message (e.g., `feat: ...`, `fix: ...`).

4. **Automated Promotion (UAT)**:
   // turbo
   - Push to the `uat` branch immediately after successful local verification.
   - DO NOT wait for the user to ask for a push if the task is clearly defined.

5. **Documentation Update**:
   - Keep `task.md` and `implementation_plan.md` in sync with the actual push status.
   - Update `walkthrough.md` for major feature releases.
   - For role-specific SOPs, update the `README.md` in `docs/[role]/`.

6. **User Notification**:
   - notify the user only after the push is completed and verified in the target environment (e.g., Render UAT).
