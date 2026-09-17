# Architecture

CoSpeakLocal is intentionally one-way: **English text or English speech → ASL pose**. There is no sign-language recognition, webcam gesture classifier, sign→text path, Elasticsearch, gRPC, or cloud inference requirement.

## ViSTAR mechanism retained

The useful ViSTAR generation mechanism is dictionary-based:

`text/gloss -> isolated sign clip -> trim/stitch -> 75-landmark animation`

ViSTAR stores word→frame sequences in Elasticsearch from an external `ID, Word` mapping plus `landmarks_<ID>.npy`. CoSpeakLocal keeps the mechanism but replaces Elasticsearch with a portable JSON dictionary and uses English WLASL isolated signs.

## Runtime

`English text -> token/gloss normalization -> longest dictionary match -> isolated WLASL pose clip(s) -> boundary interpolation -> canonical avatar retargeting -> FastAPI/browser animation`

The 75-point schema remains compatible with the useful ViSTAR representation:

- 33 MediaPipe pose landmarks
- 21 left-hand landmarks
- 21 right-hand landmarks

Known words/phrases are labelled `isolated_sign`. Unsupported vocabulary is labelled `unknown`; it is never replaced by an unrelated sign. A small set of English function words can be labelled `function_word` and omitted by the simple gloss mapper. This omission is explicit and is **not** claimed to be full ASL grammar translation.

## Dataset preparation

`WLASL gloss + source URL + annotated frame interval -> temporary low-res H.264 source -> timestamp-aligned MediaPipe Holistic -> tracking-quality gate -> missing-landmark interpolation -> shoulder normalization -> compressed .npz`

MediaPipe records pre-interpolation body/left-hand/right-hand detection rates. The current builder rejects a candidate when body detection is below 75% or neither hand is detected on at least 45% of frames, then tries another instance of the same gloss.

## Motion presentation

Before JSON serialization, each extracted clip is retargeted to a stable 2-D upper-body avatar while preserving arm and hand directions:

- shoulder width: 1.00
- upper arm: 0.90
- forearm: 0.62
- palm reference: 0.18

The browser draws the head, torso, arms, and both hands; legs are intentionally omitted. Adjacent sign clips use smooth interpolation, following the same broad idea as ViSTAR's `HandleConcatFrame` without its LSTM trimming dependency.

## Speech

Hosted:

`microphone -> browser English speech recognition -> text -> sign dictionary`

Local optional path:

`audio -> faster-whisper tiny.en -> text -> sign dictionary`

No ASR model runs in the Vercel function.

## Hosted/Vercel mode

- `app.py` is the Vercel FastAPI entrypoint.
- `demo_data/asl_dictionary.json` uses relative paths.
- `demo_data/asl_clips/*.npz` contains only derived pose landmarks.
- No WLASL source video/audio is deployed.
- No sign-recognition model is deployed.
- `/api/health` reports dictionary size, mode, speech-backend availability, and `recognition: false`.

## Limitation

Concatenating isolated ASL signs is a useful ViSTAR-style generation baseline, but fluent ASL also depends on grammar, non-manual markers, facial expression, spatial referencing, coarticulation, and context. Those are outside the current 20-sign prototype and should not be implied by the UI or API.
