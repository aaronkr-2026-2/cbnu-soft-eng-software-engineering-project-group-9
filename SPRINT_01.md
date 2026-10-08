# Sprint 01 — 7 October 2026

## Goal

Expand CoSpeakLocal from 20 to 300 quality-checked WLASL pose signs while keeping the deployed demo usable on Vercel.

## Prioritized backlog

| Priority | Item | Owner |
| --- | --- | --- |
| P0 | #2 Expand WLASL pose dictionary to 300 signs | Đỗ Minh Tùng |
| P0 | #3 Validate 300-sign dictionary for Vercel deployment | Đỗ Minh Tùng |
| P1 | #4 Add data-driven semantic sign retrieval | Đỗ Minh Tùng |
| P1 | #5 Add pose quality gates and regression checks | Đỗ Minh Tùng |
| P2 | #6 Improve vocabulary discovery and examples | Đỗ Minh Tùng |

## Refined work

### #2: 300-sign WLASL dictionary

Tasks: select covered glosses; extract one 543-landmark clip per gloss; reject low body/hand coverage; build the index; copy derived pose files only.

Acceptance: at least 300 unique glosses load as `MotionClip` objects; every retained clip has 543 landmarks; no raw source video/audio is committed.

### #3: Vercel validation

Tasks: generate the deploy bundle; measure bundle size; test `/api/health`; smoke-test a five-word request.

Acceptance: Vercel build completes; hosted health reports at least 300 signs; no raw media is bundled; the smoke request returns pose frames.

## Check-ins

- Daily 10-minute progress check-in: report extracted-sign count, failures, and bundle size.
- End-of-sprint review: demonstrate the hosted 300-sign dictionary and close accepted issues.

## Definition of done

- [ ] Implementation is committed and pushed.
- [ ] Automated tests pass.
- [ ] Relevant issue has tasks, owner, and acceptance checks.
- [ ] Derived data is indexed and verified; raw source media is excluded.
- [ ] Vercel deployment and smoke test succeed.
- [ ] README/API-visible sign count reflects the shipped dictionary.
