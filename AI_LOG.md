# AI_LOG.md

Every time you update your project, please make a note of what you did in the `AI_LOG.md` file, according to the following template.

---

## [Initial Push]
**Tool(s) used:** Deepseek Code
**What I asked for:** I ask for extract landmark for me and create frontend/backend for me
**What I kept as-is:**
**What I changed or rejected, and why:** Initial project
**Something the AI got wrong that I had to catch:** Stich/combine pose completely wrong, no smooth, need to rewrite by hand

---

## Sprint 01 planning — 7 October 2026

**Tool(s) used:** DeepSeek

**What I asked for:** Create a short sprint plan, prioritize the 300-sign WLASL expansion, and prepare the product backlog.

**What I kept as-is:** The existing WLASL pose pipeline and the 20-sign MVP dictionary.

**What I changed or rejected, and why:** Added a linked sprint backlog and focused the first sprint on a local 300-sign WLASL build so the dictionary can grow without raw-video downloads.

**Something the AI got wrong that I had to catch:** None recorded for this milestone.

---

## Architecture documentation and Sprint 1 review — 20 October 2026

**Tool(s) used:** Codex

**What I asked for:** Write architecture documentation and diagrams, update the README, and record Sprint 1 completion.

**What I kept as-is:** The existing application architecture and completed WLASL dictionary expansion.

**What I changed or rejected, and why:** Removed dataset counts, file sizes, and low-level details from the architecture overview to keep it general.

**Something the AI got wrong that I had to catch:** The first architecture draft included unnecessary dataset statistics.

**Result:** Sprint 1's dictionary-expansion goal is complete. Remaining backlog items are follow-up work.

---

## Searchable dictionary and pose investigation — 12 November 2026

**Tool(s) used:** Codex

**What I asked for:** Let visitors browse supported words instead of guessing, and investigate detached hands in the expanded poses.

**What I kept as-is:** The active dictionary, source clips, and pose playback pipeline.

**What I changed or rejected, and why:** Added a dictionary API, searchable word buttons, retry feedback, tests, and documentation. Kept pose-quality work open: adding vocabulary does not mean all clips are visually correct.

**Something the AI got wrong that I had to catch:** Expanded clips can show detached hands. Tracking errors and absolute-position gap filling need further repair and visual review.

**Result:** Dictionary API and interaction checks pass (27 Python tests and 2 JavaScript tests). Pose defects were investigated, not repaired in this update.

## Hand-track repair — 12 November 2026

**Tool used:** Codex

**Request:** Fix broken new poses and reprocess source data where needed.

**Changes:** Reject detached hand tracks, fill short gaps relative to the wrist, preserve missing long gaps, and connect displayed forearms to tracked hand roots. Reprocessed the bundle and re-extracted coffee, book, and drink. Added an explicit option for already-trimmed local videos.

**What was wrong:** Absolute-position interpolation could freeze hands, and full-video annotation offsets were incorrectly reused for some already-cut local clips.

**Validation:** 32 Python tests and 2 JavaScript tests pass; coffee's replacement tracks both hands throughout, with sampled pose frames visually inspected. Full dictionary visual/linguistic review remains open; filtering is not recovery of unobserved motion.
