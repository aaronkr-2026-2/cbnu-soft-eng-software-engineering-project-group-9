# Sprint 01 — 7 October 2026

## Goal

Expand CoSpeakLocal from 20 to 300 quality-checked WLASL pose signs while keeping the deployed demo usable on Vercel.

## Prioritized backlog

**Status: Complete — sprint goal achieved.** Reviewed on 20 October 2026.

The dictionary expansion and deployment tasks (#2 and #3) are complete. The production health endpoint reports the expanded vocabulary. The implementation passed 25 automated tests during delivery.

Items #4 and #5 remain follow-up work. Vocabulary discovery for #6 was implemented after the sprint; deployment review and issue closure are tracked separately.

| Priority | Item | Owner |
| --- | --- | --- |
| P0 | #2 Expand WLASL pose dictionary to 300 signs | Đỗ Minh Tùng |
| P0 | #3 Validate 300-sign dictionary for Vercel deployment | Đỗ Minh Tùng |
| P1 | #4 Add data-driven semantic sign retrieval | Đỗ Minh Tùng |
| P1 | #5 Add pose quality gates and regression checks | Đỗ Minh Tùng |
| P2 | #6 Improve vocabulary discovery and examples — searchable dictionary implemented | Đỗ Minh Tùng |

## Refined work

### #2: 300-sign WLASL dictionary

Tasks: select covered glosses; extract one 543-landmark clip per gloss; reject low body/hand coverage; build the index; copy derived pose files only.

Acceptance: at least 300 unique glosses load as `MotionClip` objects; every retained clip has 543 landmarks; no raw source video/audio is committed.

### #3: Vercel validation

Tasks: generate the deploy bundle; measure bundle size; test `/api/health`; smoke-test a five-word request.

Acceptance: Vercel build completes; hosted health reports at least 300 signs; no raw media is bundled; the smoke request returns pose frames.

## Check-ins

### Follow-up — 12 November 2026

Owner: Đỗ Minh Tùng.

- [x] Expose canonical words through `GET /api/dictionary`, without internal file paths.
- [x] Add searchable word buttons that append words or phrases to the input.
- [x] Handle loading failures, retry, and searches with no results.
- [x] Verify API and interaction behavior with automated tests.
- [ ] Check the deployed dictionary on desktop and mobile before closing #6.
- [ ] Under #5, repair and visually review hand-tracking defects in expanded clips. Coffee, book, and drink show hand/body wrist disagreement; interpolation can preserve misplaced or stale hand positions.

Validation: 27 Python tests and 2 JavaScript interaction tests pass. These tests do not establish visual or linguistic correctness of the pose dataset. Sprint 1 completion refers to dictionary expansion, not completion of pose-quality review.

- Daily 10-minute progress check-in: report extracted-sign count, failures, and bundle size.
- End-of-sprint review: demonstrate the hosted 300-sign dictionary and close accepted issues.

## Definition of done

- [x] Implementation is committed and pushed.
- [x] Automated tests pass.
- [x] Relevant issue has tasks, owner, and acceptance checks.
- [x] Derived data is indexed and verified; raw source media is excluded.
- [x] Vercel deployment and smoke test succeed.
- [x] README/API-visible sign count reflects the shipped dictionary.
