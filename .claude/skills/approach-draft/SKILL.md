---
name: approach-draft
description: Turn a matched signal + enriched contact into a ready-to-send first-touch email the owner can approve with one swipe. Use when a signal fires on an account with contacts, when asked to "draft the approach", "write the outreach", or as step 4 of /goal. Never sends anything — writes to gtm_approach_draft for human approval.
---

# Approach draft — the money step

One signal + one contact → one short email that proves we know about THEIR project. In a finite market you get one first impression per account and there are only ~23 accounts: **a burned prospect is a % of TAM lost forever.**

## Inputs

The signal (what happened, source, date), the account (name, city, what they operate), the contact (name, role), the user's profile (what they sell, their words from onboarding).

## Draft rules

- **Language of the recipient** (French for FR accounts). Plain words, zero marketing tone — this is one plant person writing to another.
- **Open with their project, not with us**: reference the specific signal (the tender, the extension, the new line) in sentence 1. That reference IS the personalization; no flattery padding.
- 4-6 sentences max. One concrete offer of value tied to the signal (not a generic pitch). One low-friction CTA (a 15-min call, "je peux vous envoyer X").
- No jargon, no "synergies", no exclamation marks, no "j'espère que vous allez bien".
- Never invent facts about their project beyond the signal's evidence. If the signal says "permit for 24,000 m² extension", we may say that; we may not say "your new production line".

## Output

- Write to the company's `gtm_approach_draft` property + a note with the full draft and the signal reference.
- Status stays **pending human swipe**. This skill NEVER sends. The human gate is a feature ("never burn a prospect"), not a limitation — say so in the demo.
- Batch report: "K drafts ready for review" → these feed the swipe UI queue (`gtm_priority = hot` + `gtm_approach_draft` set).
