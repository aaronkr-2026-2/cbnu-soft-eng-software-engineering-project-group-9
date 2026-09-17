# ViSTAR review for CoSpeakLocal

ViSTAR contains both sign→text recognition and text→sign generation. CoSpeakLocal keeps the **generation-side isolated-sign dictionary mechanism** and removes the recognition side.

## What ViSTAR actually does on generation

The relevant ViSTAR path uses an external mapping table (`ID`, `Word`) plus isolated landmark arrays named like `landmarks_<ID>.npy`. Its loader inserts those word→motion records into Elasticsearch. At runtime, text/glosses retrieve isolated sign sequences and `HandleConcatFrame` trims/interpolates sequence boundaries.

The original isolated-sign files are not committed in the ViSTAR repository; `src/init_data/updata.py` points to external developer-machine paths. Therefore CoSpeakLocal cannot simply copy ViSTAR's dataset and instead needs an English isolated-sign source.

## What CoSpeakLocal retains

- 75-point representation: 33 pose + 21 left hand + 21 right hand.
- MediaPipe-based landmark extraction and normalization.
- **word/gloss → isolated sign motion** dictionary generation.
- Temporal interpolation between isolated signs.
- Browser rendering of upper body and both hands.

## English replacement for ViSTAR's external dictionary

CoSpeakLocal uses WLASL word-level/isolated ASL metadata and source intervals to construct its own MediaPipe landmark dictionary. The runtime JSON dictionary replaces Elasticsearch so the app stays small and portable.

Current production flow:

`English text/speech -> simple gloss mapping -> WLASL isolated sign clip(s) -> smooth stitching -> canonical upper-body avatar`

## Deliberately removed

- sign-language recognition/classification;
- camera→text;
- Vietnamese tokenizer/NER pipeline;
- Elasticsearch;
- gRPC multi-service architecture;
- auth/database layers;
- Windows/macOS hard-coded paths.

The absence of recognition does **not** mean sign-language data is absent: isolated ASL data is now the primary generation dictionary, exactly matching the design intent that was originally missed.
