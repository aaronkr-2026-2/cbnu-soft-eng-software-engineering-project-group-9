# CoSpeakLocal

Small, English-only **text/speech → isolated ASL pose** prototype.

## MVP Status

Sprint 1 is complete: the WLASL pose dictionary has been expanded to 300 signs and is deployed on Vercel. Semantic retrieval and vocabulary discovery remain planned follow-up work.

Speech input uses browser speech recognition; local audio transcription is available with faster-whisper.

## Documentation

- [Software architecture and diagrams](docs/architecture.md)
- [Sprint 1 results and backlog](SPRINT_01.md)

## Product vision

### What

CoSpeakLocal retrieves sign motions from an expandable dictionary, connects them into a smooth visual sequence, and displays body, hand, and facial landmarks in real time.

### Who

It is for Deaf and hard-of-hearing people, sign-language learners, educators, accessibility-focused teams, and developers building English-to-sign visual communication tools.

### Why

Spoken-language information is often inaccessible or delayed for sign-language users. CoSpeakLocal makes everyday English available as a visual, pose-based representation that can be viewed, studied, and improved without serving raw source video.

### For

- Quick conversion of common English words and phrases into sign motion
- Sign-language learning and demonstration
- Accessible communication prototypes
- Research and development of larger sign-language tools
- A sign dictionary that can grow through new labelled motion clips and NLP-based retrieval
- University, School teaching
