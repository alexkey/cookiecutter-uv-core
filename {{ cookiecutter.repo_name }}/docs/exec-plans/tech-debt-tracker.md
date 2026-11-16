# Tech-debt tracker

This file lists work that was knowingly deferred: shortcuts taken on purpose, follow-ups
outside the scope of an execution plan, findings noticed but not fixed, and test targets
that were declined. Fix or report a defect that blocks current work instead of listing
it here.

Add an entry when the debt is recorded, and remove it in the change that resolves it.
Dates are in UTC. The `develop` skill maintains this file alongside the execution plans
in `active/` and `completed/`.

## Format

    ### <Short title>

    - Recorded: YYYY-MM-DD
    - Source: <execution plan or task that recorded the debt>
    - Location: <files or components>
    - Debt: <what is missing or wrong, and its consequence>
    - Remedy: <the change that resolves it>

## Entries
