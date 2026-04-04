# Task Files

This directory contains task tracking files for the project.

## Organisation

- Each task file represents a logical feature or work stream
- Files are prefixed with ISO-8601 date: `YYYY-MM-DD-feature-name.md`
- Example: `2026-03-21-galaxy-generation.md`

## Benefits

- Avoids merge conflicts when working on multiple features
- Preserves historical record of what was done and when
- Makes it easy to find current work (latest date)

## Usage

1. When starting new work, create a new dated task file
2. Mark checkboxes `[x]` as tasks are completed
3. Completed task files remain as historical documentation
4. Current work is always in the most recent file (by date)

## Finding Current Work

To see what's in progress:
```bash
ls -t tasks/*.md | head -1  # Shows most recent task file
```
