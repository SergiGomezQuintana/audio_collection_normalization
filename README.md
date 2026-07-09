# BS1770 Audio Collection Normalizer

A desktop application for loudness normalization of audio collections according to the **ITU-R BS.1770** recommendation.

The application analyzes every audio file in a folder, measures its integrated loudness (LUFS) and True Peak level, computes the appropriate gain adjustment, and writes normalized copies while preserving the original audio format and encoding settings whenever possible.

Unlike traditional peak normalization, this tool aims to achieve consistent **perceived loudness** across an entire collection while ensuring that no track exceeds a configurable True Peak limit.

---

## Features

* Graphical user interface for Windows and macOS
* ITU-R BS.1770 loudness measurement
* K-weighting filter
* Integrated LUFS calculation with absolute and relative gating
* True Peak estimation using 4× oversampling
* Automatic collection-wide loudness target
* Manual LUFS target
* Configurable True Peak limit
* Batch processing of entire folders
* Live progress and processing log
* CSV normalization report
* Preserves the original audio format and encoding settings whenever supported

---

## Supported formats

The application currently supports reading and writing:

* MP3
* WAV
* FLAC
* AIFF
* AAC / M4A
* OGG Vorbis
* Opus

Additional formats supported by FFmpeg can be added with minimal changes.

---

## Why this tool?

Most audio normalization utilities simply force every file to reach the same loudness target.

Although effective, this may require reducing the gain of already loud tracks to satisfy a fixed target or increasing quieter tracks until clipping occurs.

This application offers two operating modes:

### Automatic Target

The program analyzes the complete collection before any processing takes place.

It then computes the **highest common loudness** that every track can safely reach without violating the selected True Peak limit.

This maximizes playback loudness while preventing clipping.

### Fixed Target

Alternatively, a user-defined LUFS target may be specified.

In this mode, each track is normalized toward the requested loudness while still respecting the configured True Peak limit.

---

## Processing pipeline

### Pass 1 – Analysis

Each audio file is decoded into floating-point PCM samples using FFmpeg.

The program then computes:

* Integrated Loudness (LUFS)
* Relative gating threshold
* Number of analysis blocks
* Number of gated blocks
* True Peak (dBTP)
* Duration
* Sample rate

When Automatic Target mode is enabled, the collection-wide target loudness is computed from the analyzed tracks.

---

### Pass 2 – Gain application

For every track, two gain values are computed:

* Gain required to reach the target loudness
* Maximum gain allowed by the True Peak limit

The smaller of the two values is applied.

The normalized audio is then re-encoded using FFmpeg while preserving the original:

* File format
* Codec
* Sample rate
* Channel count
* Bitrate (where applicable)

---

## Graphical interface

The application provides:

* Input folder selection
* Output folder selection
* Automatic or manual LUFS target
* Configurable True Peak limit
* Progress bar
* Live processing log

---

## Output

The normalized files are written to the selected output directory.

A CSV report named

`normalization_report.csv`

is also generated containing:

* Original LUFS
* True Peak
* Applied gain
* Predicted loudness
* Limiting factor (Loudness or True Peak)
* Processing parameters

---

## Technical implementation

This implementation follows the ITU-R BS.1770 recommendation for:

* K-weighting filter
* 400 ms analysis blocks
* 100 ms block spacing
* Absolute gate at −70 LUFS
* Relative gate at 10 LU below integrated loudness
* Integrated loudness calculation
* True Peak estimation using 4× oversampling

The following features extend beyond the standard:

* Automatic collection-wide target estimation
* Batch normalization workflow
* Preservation of original encoding settings
* CSV reporting
* Progress reporting and GUI

---

## Building from source

Requirements:

* Python 3.11 or newer
* FFmpeg
* NumPy
* SciPy
* SoundFile

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the graphical interface:

```bash
python gui.py
```

---

## Releases

Precompiled executables for Windows and macOS are available in the GitHub Releases section.

No Python installation or external FFmpeg installation is required.

---

## License

Released under the MIT License.
