# scoreflow
# ScoreFlow

**AI-assisted music notation from audio.**

ScoreFlow turns a raw audio recording into an editable, printable music score, and uses AI to help fill in missing parts of an arrangement.

## What it does

1. **Upload** any audio recording of a song.
2. **Separate** the track into individual components (vocals, drums, bass, other) using machine learning.
3. **Transcribe** each component into pitched notes with timing and rhythm.
4. **Visualize** the result as a real, editable SATB (Soprano-Alto-Tenor-Bass) score in the browser, not just a waveform or audio playback.
5. **Predict** (stretch goal): give the model a few seed notes of a bassline or voice part, and it predicts a musically coherent completion for the rest of the part.

The core idea is to remove the manual transcription bottleneck that currently makes arranging music slow, and replace it with an AI-assisted pipeline that produces actual notation an arranger can use and edit, not just audio.

## Why it matters

Existing notation tools (Sibelius, Noteflight) require the arranger to transcribe everything by ear and by hand. ScoreFlow automates the transcription step, and goes a step further by attempting to generate missing harmony or bass parts, targeting the specific, time-consuming task of writing out inner voices for an arrangement.

## How it works (pipeline)

| Stage | Tool | Purpose |
|---|---|---|
| Source separation | Demucs (Meta) | Splits audio into vocal/instrument stems |
| Audio-to-MIDI | Basic Pitch (Spotify) | Converts each stem into notes with pitch, timing, rhythm |
| MIDI-to-notation | music21 | Converts MIDI into MusicXML (standard notation format) |
| Rendering | OpenSheetMusicDisplay / VexFlow | Displays MusicXML as an engraved, playable score in-browser |
| Part completion | MusicGen / GPT-4o, benchmarked against an LSTM baseline | Given seed notes, predicts a full bass or harmony line |

## Research question

Given a partial melodic or harmonic line, can a generative model predict a musically coherent completion that an arranger would actually find useful? ScoreFlow evaluates three approaches (MusicGen, GPT-4o audio, and an LSTM baseline trained on SATB choral music) against pitch accuracy, rhythmic coherence, and acceptance from a small user study of working musicians.

## Deliverables

- A semi-functioning web app: upload audio, transcribe it, visualize the notes.
- A real song arranged end-to-end using the tool.
- Performance comparison graphs across the three completion models.

## Status

Project proposal stage, Dartmouth College, May 2026. Built by Brenda Waiya.
