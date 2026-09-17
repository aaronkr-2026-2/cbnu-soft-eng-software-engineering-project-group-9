# Dataset plan

## Primary: WLASL isolated ASL

CoSpeakLocal's generation dictionary now uses WLASL because the target mechanism is the same one used on ViSTAR's generation side: **word/gloss → isolated sign motion clip → stitch clips**.

WLASL is a large-scale **word-level / isolated American Sign Language** dataset with a 2,000-gloss vocabulary. Its metadata provides glosses, source URLs, signer/source identifiers, and exact annotated frame boundaries. CoSpeakLocal uses only those annotations to locate an isolated sign segment, then independently re-extracts a 75-landmark MediaPipe representation.

### Current seed dictionary

The validated seed contains 20 glosses:

`hello, thank you, yes, no, please, sorry, help, good, bad, love, you, i, we, what, where, how, name, friend, want, need`

All 20 produced usable MediaPipe clips. The resulting hosted derivative bundle contains:

- 20 isolated signs
- 994 landmark frames
- 75 landmarks per frame
- about 745 KB compressed motion data
- no source video
- no source audio
- no recognition model

Example extraction quality:

- `hello`: 47 frames, body detection 100%, right-hand detection ~97.9%
- `help`: 47 frames, body 100%, left hand ~93.6%, right hand 100%
- `love`: 40 frames, body/left/right all 100%
- `what`: 33 frames, body/left/right all 100%
- `name`: 43 frames, body/left/right all 100%

### Build

```bash
python scripts/fetch_ytdlp.py
python scripts/prepare_wlasl_dictionary.py \
  --glosses 'hello,thank you,yes,no,please,sorry,help,good,bad,love,you,i,we,what,where,how,name,friend,want,need'
python scripts/make_deploy_bundle.py
```

The builder downloads low-resolution H.264 source media temporarily, converts the WLASL 25-fps frame annotations to timestamps, extracts only the annotated sign interval with MediaPipe Holistic, and deletes source media afterward. If a source is unavailable or landmark coverage is poor, it tries another WLASL instance for that gloss.

### Usage rights

The upstream WLASL project states that WLASL is for academic/computational use and explicitly disallows commercial usage. Accordingly, this WLASL-backed build is for the current research/hackathon demo. Commercial productization requires a separately licensed sign corpus or explicit permission appropriate to the intended use.

## Previous experiment: TED Gesture-Type

The earlier CoSpeakLocal prototype used TED Gesture-Type English **co-speech gestures**. That was the wrong primary dataset for the user's intended ViSTAR-like sign-generation mechanism. Its extraction/retrieval scripts remain in the repository as experimental utilities, but the production app and Vercel bundle no longer use TED motion.

## Why not use WLASL for recognition here?

WLASL is often used for isolated-sign recognition research, but CoSpeakLocal uses its clips only as a **generation dictionary**. There is no camera input, classifier, sign recognition endpoint, or sign→text model in the product.

## Future continuous-sign path

A larger dictionary can expand lexical coverage, but dictionary concatenation alone does not solve fluent continuous ASL. A later generation model should address English→ASL gloss/grammar translation, non-manual signals and facial expression, spatial referencing, and transition/coarticulation quality while preserving the `[T,75,3]` runtime interface.
