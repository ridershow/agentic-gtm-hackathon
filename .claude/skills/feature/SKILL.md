---
name: feature
description: Git branching workflow for this hackathon repo — branch-per-feature, commit hygiene, and PR flow. Use whenever anyone starts new work (a feature, fix, or experiment), wants to create a branch, is about to commit or push, or wants to ship work and open a PR. Trigger on "start working on X", "new feature", "create a branch", "commit this", "push", "ship it", "open a PR", "merge this" — even when git isn't mentioned explicitly. Also trigger BEFORE writing code for any new piece of work if we're currently on main.
---

# Feature branch workflow

## The one rule

**`main` is the demo branch.** The 2-minute demo runs off `main`, so it must be working at all times. Nobody commits directly to it — all work happens on short-lived feature branches merged back via PR. With several people building in parallel on a one-day deadline, this is what prevents a broken demo an hour before pitching.

## Starting work: `/feature <what you're building>`

When someone describes new work (e.g. `/feature sillage intent scoring`), set them up on a fresh branch:

1. **Check for uncommitted changes** (`git status`). If tracked files are modified or staged, don't silently drag them along — tell the user what's uncommitted and ask whether to commit it on the current branch first, bring it to the new branch, or park it. Resolve this *before* touching main: a dirty tree can make the checkout/pull below fail. To bring changes along, `git stash`, do step 2, then `git stash pop` on the new branch. Untracked files are fine — they follow along across checkouts; just proceed.
2. **Branch off fresh main:**
   ```bash
   git checkout main && git pull origin main
   git checkout -b <type>/<kebab-slug>
   git push -u origin <type>/<kebab-slug>
   ```
   Push immediately so teammates can see who's working on what (`git branch -r`).
3. Confirm to the user: branch name + a reminder to `/feature ship` when done.

### Branch naming

`<type>/<short-kebab-slug>` — types: `feat` (new capability), `fix` (repair), `chore` (setup, config, docs). Derive the slug from what the user said, 2-4 words max.

- "sillage intent scoring" → `feat/sillage-intent-scoring`
- "fix the BOAMP date parsing" → `fix/boamp-date-parsing`
- "add streamlit config" → `chore/streamlit-config`

If a branch with that name already exists, someone may already be on it — say so and suggest either joining that branch or picking a more specific slug.

## While working: commits

Commit early and often — every time something works, not one giant commit at the end. Small commits are what make it possible to salvage a branch when an experiment goes sideways at hour 6.

Format: `type: short imperative summary` (e.g. `feat: map ICPE filings to site operators`, `fix: handle empty SITADEL responses`). No need for scopes or bodies today — speed over ceremony.

**Never commit secrets.** API keys (Anthropic, FullEnrich, Sillage) live in `.env`, which is gitignored. If a key shows up in a diff, stop and move it to `.env` before committing. Leaked keys in a public hackathon repo get scraped in minutes — and this team really should not be the one leaking secrets on GitHub.

## Shipping: `/feature ship`

When work on a branch is done:

1. Commit anything outstanding (ask before bundling unrelated changes).
2. **Sync with main first** — others merge fast today, so main moves:
   ```bash
   git fetch origin && git merge origin/main
   ```
   Merge, don't rebase — it's faster to resolve and nobody needs a clean history today. If there are conflicts, resolve them here on the branch (never on main), and verify the app still runs before continuing.
3. **Push and open the PR:**
   ```bash
   git push
   gh pr create --title "<type>: <summary>" --body "<2-3 lines: what it does, how to check it works>"
   ```
4. **Merge fast, squash, clean up.** Ping a teammate for a quick look, but don't block on formal review — long-lived branches are a bigger risk than lightly-reviewed code today. Once green:
   ```bash
   gh pr merge --squash --delete-branch
   git checkout main && git pull
   ```
5. Tell the team main moved, so everyone merges fresh main into their branch soon after.

## Recovery

- **"I accidentally committed on main"** (locally, not pushed): move the commits to a branch and reset main —
  ```bash
  git checkout -b feat/<slug>        # branch keeps the commits
  git checkout main
  git reset --hard origin/main       # main back to remote state
  git checkout feat/<slug>
  ```
- **"My branch conflicts with main"**: merge `origin/main` into the branch and resolve there (step 2 of shipping). Ask the person who touched the same file if intent is unclear — they're in the same room.
- **Never** force-push `main`, and never `git reset --hard` anything that isn't already safe on the remote without confirming with the user first.
