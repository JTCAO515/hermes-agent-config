# Find Skills — External Skill Discovery

> Absorbed from standalone `find-skills` skill (archived). Part of the skill lifecycle pipeline managed by `skillify`.

## When to Use This

- User asks "how do I do X" where X might be a common task with an existing skill
- User says "find a skill for X" or "is there a skill for X"
- User wants to search for tools, templates, or workflows
- User mentions they wish they had help with a specific domain

## The Skills CLI

`npx skills` is the package manager for the open agent skills ecosystem.

**Key commands:**

- `npx skills find [query]` — Search for skills interactively or by keyword
- `npx skills add <package>` — Install a skill from GitHub or other sources
- `npx skills check` — Check for skill updates
- `npx skills update` — Update all installed skills

Browse skills at: https://skills.sh/

## How to Help Users Find Skills

### Step 1: Understand What They Need

Identify the domain (React, testing, design, deployment), the specific task, and whether this is common enough that a skill likely exists.

### Step 2: Search

```
npx skills find [query]
```

Examples:
- React performance → `npx skills find react performance`
- PR reviews → `npx skills find pr review`
- changelog → `npx skills find changelog`

### Step 3: Present Options

Include the skill name, what it does, install command, and link to skills.sh.

### Step 4: Offer to Install

```
npx skills add <owner/repo@skill> -g -y
```

## Common Skill Categories

| Category | Example Queries |
|----------|----------------|
| Web Development | react, nextjs, typescript, tailwind |
| Testing | testing, jest, playwright |
| DevOps | deploy, docker, kubernetes |
| Documentation | docs, readme, changelog |
| Code Quality | review, lint, refactor |
| Design | ui, ux, design-system |
| Productivity | workflow, automation, git |

## When No Skills Are Found

1. Acknowledge no existing skill was found
2. Offer to help directly
3. Suggest `npx skills init my-xyz-skill` to create their own
