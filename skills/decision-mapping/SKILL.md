---
name: decision-mapping
description: Turn a loose idea into a sequenced map of investigation tickets, then drive them to resolution one at a time.
disable-model-invocation: true
---

This skill is invoked when a loose idea requires more than one agent session to turn into a plan. It creates a stateful decision map in a markdown file, and drives the user through a sequence of tickets to resolve the open questions — which may require either prototyping, research or discussion.

## The Decision Map

The decision map is a single compact Markdown file, one per planning effort, git-tracked alongside the project. It is the canonical artifact — the **whole map is loaded as context into every session**, so it must stay compact.

Assets created during tickets should be linked to from the map, not duplicated within it.

### Structure

Numbered entries ("tickets"), each its own section keyed by its number. Each ticket must be sized to one 100K token agent session.

## Ticket Types

Three types: investigation, prototype, discussion.

## Fog of war

The map is *deliberately* incomplete beyond the frontier. Your job is to investigate the frontier, and to resolve tickets in order to push the frontier forward. Push back the fog of war, one node at a time.

At some point, the fog of war should have been pushed back far enough that the path to the finish line is clear. At that point, no more tickets will be required and the decision map can be considered 'done'.

## Invocation

Two ways: **bootstrap** (user invokes with a loose idea) and **resume** (user invokes with a path to an existing map and a ticket number).

If the decisions made invalidate other parts of the map, update or delete those nodes.

## Parallelism

The user may choose to run tickets in parallel, so expect other agents to make changes to the map.

## Skipping The Decision Map

Many times, the initial grilling will result in no fog of war. No unresolved tickets. Nothing to do, except implement.

In those situations, you should offer the user the chance to skip the decision map — since the decision map is only needed if multi-session decisions need to be made.

If they skip it, you should recommend either implementing directly or using `/to-prd` to schedule a multi-session implementation.
