---
name: daily-tasks
version: 1.0.0
description: |
  Daily task management and morning preparation workflow. Combines task lifecycle
  (add, complete, defer, review) with morning prep (calendar lookahead, meeting
  context, open threads). Brain-backed task list at ops/tasks.md.
triggers:
  - "add task"
  - "complete task"
  - "what are my tasks"
  - "task list"
  - "defer task"
  - "morning prep"
  - "prepare for today"
  - "what's on my plate"
  - "day prep"
tools:
  - search
  - get_page
  - put_page
  - add_timeline_entry
  - query
  - list_pages
  - get_timeline
mutating: true
writes_pages: true
writes_to:
  - ops/tasks.md
---

# Daily Tasks — Task Management + Morning Preparation

> Umbrella skill absorbing `daily-task-manager` and `daily-task-prep` (archived 2026-06-02).

Two modes sharing the same brain-backed task infrastructure.

---

## Mode A: Task Manager

### Phases

1. **Load current tasks.** `gbrain get ops/tasks` — read the task list.
2. **Execute the requested action:**
   - **Add:** Append task with priority (P0-P3), description, due date. Add timeline entry.
   - **Complete:** Mark as done, move to completed section with date.
   - **Defer:** Move to next day/week with reason.
   - **Remove:** Delete from list (rare, prefer complete or defer).
   - **Review:** Display all active tasks by priority.
3. **Save.** `gbrain put ops/tasks` — write updated task list.

### Priority Levels

| Level | Meaning |
|-------|---------|
| P0 | Urgent — must do today |
| P1 | Today's priorities |
| P2 | This week |
| P3 | Backlog |

### Task Format

```markdown
# Tasks

## P0 — Urgent
- [ ] {task description} (due: {date})

## P1 — Today
- [ ] {task description}

## Completed
- [x] {task} (completed: {date})
```

---

## Mode B: Morning Preparation

### Phases

1. **Load calendar.** Check today's meetings. For each: load attendee brain pages, recent timeline, open threads.
2. **Check yesterday's threads.** Search brain for yesterday's timeline entries. Flag anything unresolved.
3. **Review active tasks.** Load `ops/tasks` from brain. Surface P0 and P1 items.
4. **Compile prep briefing.** Per-meeting context cards + open threads + task priorities.

### Prep Briefing Format

```text
Morning Prep — {date}

Meetings today: {N}

## {Meeting 1 title} at {time}
Attendees: {names with brain context}
Context: {recent interactions, open threads}
Prep: {what to know before this meeting}

## Open Threads
- {thread from yesterday, with context}

## Tasks (P0-P1)
- {task with priority}
```

---

## Anti-Patterns

- ❌ Adding tasks without a priority level
- ❌ Completing tasks without recording the completion date
- ❌ Deferring tasks without a reason
- ❌ Letting the task list grow unbounded (review weekly)
- ❌ Storing tasks outside the brain (they should be searchable)
- ❌ Listing meetings without loading attendee context from brain
- ❌ Ignoring yesterday's unresolved threads
