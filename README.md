# CoSpeakLocal

Small, English-only **text/speech → isolated ASL pose** prototype.

## MVP Status

Sprint 1's dictionary-expansion goal is complete. The website now includes a searchable sign dictionary: browse available words, click to add them to the input, then select **Generate motion**. The list comes from the active dictionary rather than a manually maintained word list.

Semantic retrieval remains planned. Some expanded clips have hand-tracking defects (including detached hands in coffee); vocabulary availability is not a guarantee of pose quality.

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
