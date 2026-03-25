---
description: Merge UAT to PRD to trigger production deployment on Render.
---
# /deploy Workflow
Use this command ONLY after verifying the `uat` branch using the `docs/TESTING.md` checklist.

1. **Perform Merge & Deploy**
// turbo
```powershell
./scripts/sync.ps1 -Action deploy -Message "Release version label"
```
