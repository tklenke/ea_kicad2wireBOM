# Architect Todo List

## Current Tasks

(none)

---

## Completed Tasks

### [x] Add Critical Pre-Commit Todo Review to All Roles (2025-10-18)

**Context:** Tom requested that it be CRITICAL for all roles to review and update their todo lists before every git commit.

**Changes Made:**

1. **Architect Role** (`claude/roles/architect.md:87-95`):
   - Added "CRITICAL PRE-COMMIT CHECK" section to Progress Tracking
   - 5-step mandatory checklist before every commit
   - Requires updating architect_todo.md and including it in commit
   - Emphasizes this is not optional

2. **Programmer Role** (`claude/roles/programmer.md:119-127`):
   - Added "CRITICAL PRE-COMMIT CHECK" section to Progress Tracking
   - 5-step mandatory checklist before every commit
   - Requires updating programmer_todo.md and including it in commit
   - Notes this prevents 30+ minutes of wasted verification time

3. **Code Reviewer Role** (`claude/roles/code_reviewer.md:81-95, 135-139`):
   - Added "Progress Tracking Review" as Key Activity #6
   - Added explicit verification steps for reviewing commits
   - Marked todo update as "MUST FIX" if missing
   - Added "Progress Tracking (CRITICAL)" to Review Checklist
   - 4-item checklist to verify todo list was properly updated

**Impact:** All three roles now have explicit, mandatory requirements to update their respective todo lists before committing. Code Reviewer will catch and reject commits that don't include updated todo lists.

---

### [x] Update Programmer Role Definition (2025-10-18)

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

**Resolution (2025-10-18):**

Updated `claude/roles/programmer.md` with the following improvements:

1. **Added startup verification step** (step 3 in "Always Read"):
   - Run `git log` to see recent commits
   - Run `pytest` to verify current state
   - Check what modules exist using Glob
   - Flag discrepancies between todo status and actual code state

2. **Strengthened Progress Tracking section** (section 5):
   - Marked as "CRITICAL FOR SESSION CONTINUITY"
   - Added "Why This Matters" explanation
   - Emphasized updating DURING implementation, not just at end
   - Provided clear workflow example with 7 steps
   - Explained impact: prevents wasting 30+ minutes on verification

3. **Added new "Handling Existing Code" section** (section 6):
   - Step-by-step process for verifying existing implementations
   - Guidance on when to mark tasks complete vs when to fix issues
   - Instructions to stop and ask Tom when uncertain
   - Emphasizes verifying tests are quality tests (not just mocked behavior)

These changes should significantly improve session continuity by ensuring programmers can quickly and accurately understand project state when starting work.
