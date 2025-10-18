# Architect Todo List

## Current Tasks

### Update Programmer Role Definition (2025-10-18)

**Context:** During the 2025-10-18 programmer session, we discovered that the codebase had existing implementation that was ahead of the documentation. This created confusion when starting the session.

**Issue:** The programmer role instructions in `claude/roles/programmer.md` tell the programmer to read `docs/plans/programmer_todo.md` to understand progress, but the todo document was out of sync with actual implementation.

**Changes Needed to `claude/roles/programmer.md`:**

1. **Add a startup verification step** (after reading programmer_todo.md):
   - Suggest checking git log to see recent commits
   - Suggest running tests to verify current state
   - If tests are passing but todo shows tasks incomplete, flag the discrepancy to Tom

2. **Clarify responsibility for keeping programmer_todo.md updated:**
   - Current text says to "update docs/plans/programmer_todo.md as tasks are completed"
   - Should emphasize this is CRITICAL for session continuity
   - Should happen DURING implementation, not just at end of session
   - Consider adding: "Mark tasks [~] when starting, [x] when complete and committed"

3. **Add guidance for handling existing code:**
   - What to do when code exists but documentation says it's not done
   - When to update documentation vs when to raise concerns about code quality
   - How to verify existing code meets requirements before marking tasks complete

4. **Strengthen the "Update programmer_todo.md" responsibility:**
   - Currently in section 5 "Progress Tracking" (lines 85-94)
   - Make it more prominent - maybe move earlier or add to "Key Activities"
   - Add example workflow: implement feature → tests pass → update todo → commit

**Specific Example from This Session:**
- Phase 0 tasks (0.1-0.6) were all implemented but marked `[ ]` incomplete
- Programmer had to verify each one, update tests, and mark complete
- This added ~30 minutes of verification/documentation work
- Could be avoided if previous programmer session had updated the doc

**Priority:** Medium - Affects next programmer session efficiency

---

## Completed Tasks

(none yet)
