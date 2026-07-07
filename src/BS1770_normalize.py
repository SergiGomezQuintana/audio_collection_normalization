# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 16:02:39 2026

@author: sergi
"""
# ITU BS.1770

#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import soundfile as sf
from scipy.signal import bilinear, lfilter, windows
from tqdm import tqdm
from scipy.signal import bilinear, tf2sos, sosfilt, resample_poly
import numpy as np
import csv


def ffmpeg_read(filename):
    import subprocess
    import numpy as np

    cmd = [
        "ffmpeg",
        "-i", str(filename),
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-ac", "2",
        "-ar", "44100",
        "-loglevel", "error",
        "-"
    ]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode != 0:
        raise RuntimeError(err.decode())

    audio = np.frombuffer(out, dtype=np.float32).copy()  # ✅ FIX

    audio = audio.reshape(-1, 2)

    return audio, 44100

# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------

def db(x):
    return 20.0 * np.log10(np.maximum(x, 1e-20))


def db_to_gain(db_val):
    return 10.0 ** (db_val / 20.0)

def k_weighting(fs):
    """
    ITU-R BS.1770-4 K-weighting filter.

    Parameters
    ----------
    fs : int
        Sampling frequency.

    Returns
    -------
    sos : ndarray
        Second-order sections for scipy.signal.sosfilt().
    """

    #
    # ---------------------------------------------------------
    # Stage 1 : High-shelf (+4 dB)
    #
    # H(s) =
    #
    #      s² + 129.4 s + 76655
    # -------------------------------- * 1.53512485958697
    #      s² + 676.7 s + 463361
    #
    # ---------------------------------------------------------
    #

    b = np.array([
        1.53512485958697,
        1.53512485958697 * 129.4,
        1.53512485958697 * 76655.0
    ])

    a = np.array([
        1.0,
        676.7,
        463361.0
    ])

    bz, az = bilinear(b, a, fs)

    sos1 = tf2sos(bz, az)

    #
    # ---------------------------------------------------------
    # Stage 2 : RLB high-pass
    #
    # H(s) =
    #
    #          s²
    # ----------------------
    # s² + 4636 s + 76655
    #
    # ---------------------------------------------------------
    #

    b = np.array([
        1.0,
        0.0,
        0.0
    ])

    a = np.array([
        1.0,
        4636.0,
        76655.0
    ])

    bz, az = bilinear(b, a, fs)

    sos2 = tf2sos(bz, az)

    #
    # cascade
    #

    return np.vstack((sos1, sos2))

def apply_k_weighting(y, fs):
    """
    Apply ITU-R BS.1770 K-weighting.

    Parameters
    ----------
    y : ndarray
        Shape (N,) or (N,C)

    Returns
    -------
    ndarray
        Filtered signal.
    """

    sos = k_weighting(fs)

    if y.ndim == 1:
        return sosfilt(sos, y)

    out = np.empty_like(y)

    for ch in range(y.shape[1]):
        out[:, ch] = sosfilt(sos, y[:, ch])

    return out

def block_energies(y, fs):
    """
    ITU-R BS.1770 block energies.

    Parameters
    ----------
    y : ndarray
        K-weighted signal.
        Shape (N,) or (N,C)

    fs : int
        Sample rate.

    Returns
    -------
    energies : ndarray
        Mean-square energy of each 400 ms block.

    Notes
    -----
    Blocks are:

        length = 400 ms
        hop     = 100 ms

    as required by BS.1770.
    """

    block = int(round(0.400 * fs))
    hop   = int(round(0.100 * fs))

    if y.ndim == 1:
        y = y[:, None]

    n_samples, n_channels = y.shape

    if n_samples < block:
        return np.empty(0)

    n_blocks = 1 + (n_samples - block) // hop

    energies = np.empty(n_blocks, dtype=np.float64)

    #
    # cumulative energy for every channel
    #

    cs = np.empty((n_channels, n_samples + 1), dtype=np.float64)

    for ch in range(n_channels):

        x2 = y[:, ch].astype(np.float64)
        x2 *= x2

        cs[ch, 0] = 0.0
        np.cumsum(x2, out=cs[ch, 1:])

    #
    # energy of every block
    #

    for i in range(n_blocks):

        start = i * hop
        stop  = start + block

        e = 0.0

        for ch in range(n_channels):

            e += (cs[ch, stop] - cs[ch, start]) / block

        energies[i] = e

    return energies

def integrated_loudness(energies):
    """
    Compute ITU-R BS.1770 Integrated Loudness.

    Parameters
    ----------
    energies : ndarray
        Mean-square energy of every 400 ms block.

    Returns
    -------
    dict

        {
            "lufs": float,
            "threshold": float,
            "blocks": int,
            "absolute_gated_blocks": int,
            "gated_blocks": int,
            "mean_energy": float
        }
    """

    if len(energies) == 0:

        return {
            "lufs": -np.inf,
            "threshold": -70.0,
            "blocks": 0,
            "absolute_gated_blocks": 0,
            "gated_blocks": 0,
            "mean_energy": 0.0,
        }

    energies = np.asarray(energies, dtype=np.float64)

    energies = np.maximum(energies, 1e-20)

    blocks = len(energies)

    #
    # Block loudness
    #

    loudness = -0.691 + 10.0 * np.log10(energies)

    #
    # Absolute gate
    #

    keep_abs = loudness >= -70.0

    abs_count = int(np.count_nonzero(keep_abs))

    if abs_count == 0:

        return {
            "lufs": -70.0,
            "threshold": -70.0,
            "blocks": blocks,
            "absolute_gated_blocks": 0,
            "gated_blocks": 0,
            "mean_energy": 0.0,
        }

    gated = energies[keep_abs]

    #
    # First pass
    #

    mean_energy = np.mean(gated)

    integrated = -0.691 + 10.0 * np.log10(mean_energy)

    #
    # Relative gate
    #

    threshold = integrated - 10.0

    keep_rel = loudness >= threshold

    gated = energies[keep_rel]

    gated_count = int(len(gated))

    if gated_count == 0:

        return {
            "lufs": integrated,
            "threshold": threshold,
            "blocks": blocks,
            "absolute_gated_blocks": abs_count,
            "gated_blocks": 0,
            "mean_energy": mean_energy,
        }

    #
    # Final pass
    #

    mean_energy = np.mean(gated)

    integrated = -0.691 + 10.0 * np.log10(mean_energy)

    return {

        "lufs": integrated,

        "threshold": threshold,

        "blocks": blocks,

        "absolute_gated_blocks": abs_count,

        "gated_blocks": gated_count,

        "mean_energy": mean_energy,

    }

def true_peak(y, fs, oversample=4):
    """
    ITU-R BS.1770 True Peak estimation.

    Parameters
    ----------
    y : ndarray
        Audio signal.
        Shape (N,) or (N,C)

    fs : int
        Sampling rate.

    oversample : int
        Oversampling factor.
        BS.1770 recommends at least x4.

    Returns
    -------
    float
        True Peak in dBTP.
    """

    if y.ndim == 1:
        y = y[:, None]

    peak = 0.0

    for ch in range(y.shape[1]):

        #
        # Polyphase FIR interpolation
        #

        x = resample_poly(
            y[:, ch],
            up=oversample,
            down=1,
            padtype="line"
        )

        p = np.amax(np.abs(x))

        if p > peak:
            peak = p

    return 20.0 * np.log10(max(peak, 1e-20))

def analyze_track(y, fs):
    """
    Analyze one track according to ITU-R BS.1770.
    """

    yk = apply_k_weighting(y, fs)

    energies = block_energies(yk, fs)

    loudness = integrated_loudness(energies)

    tp = true_peak(y, fs)

    return {

        **loudness,

        "true_peak": tp,

        "sample_rate": fs,

        "duration": len(y) / fs

    }

def compute_gain(stats, target_lufs=-23, tp_limit=-1):

    gain_lufs = target_lufs - stats["lufs"]

    gain_tp = tp_limit - stats["true_peak"]

    return {

        "gain_lufs": gain_lufs,

        "gain_tp": gain_tp,

        "gain": min(gain_lufs, gain_tp)

    }

def normalize_folder(
    in_folder,
    out_folder,
    target_lufs="auto",
    true_peak_limit=-1.0
):

    in_folder = Path(in_folder).expanduser().resolve()
    out_folder = Path(out_folder).expanduser().resolve()
    out_folder.mkdir(parents=True, exist_ok=True)

    files = sorted(in_folder.glob("*.mp3"))

    if len(files) == 0:
        raise RuntimeError(f"No mp3 files found in {in_folder}")

    # ----------------------------------------------------------
    # PASS 1 : ANALYSIS
    # ----------------------------------------------------------

    analysis = []

    # print("\nAnalysing collection:\n")

    for fn in tqdm(files, desc="Analysing collection"):

        y, fs = ffmpeg_read(fn)

        stats = analyze_track(y, fs)

        analysis.append({
            "file": fn,
            "stats": stats,
        })

    # ----------------------------------------------------------
    # AUTO TARGET
    # ----------------------------------------------------------

    auto_mode = (target_lufs == "auto")

    limiting_track = ""
    limiting_stats = None

    if auto_mode:

        candidates = [

            item["stats"]["lufs"]
            + true_peak_limit
            - item["stats"]["true_peak"]

            for item in analysis

        ]

        idx = int(np.argmin(candidates))

        target_lufs = candidates[idx]

        limiting_track = analysis[idx]["file"].name

        limiting_stats = analysis[idx]["stats"]

    # ----------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------

    print()
    print("=" * 64)

    print(f"Tracks analysed : {len(files)}")

    print(
        f"Target LUFS     : {target_lufs:.2f} "
        f"({'AUTO' if auto_mode else 'FIXED'})"
    )

    print(
        f"True Peak limit : {true_peak_limit:.2f} dBTP"
    )

    if auto_mode:

        print(f"Limiting track  : {limiting_track}")

        print(
            f"Track LUFS      : {limiting_stats['lufs']:.2f}"
        )

        print(
            f"Track TruePeak  : {limiting_stats['true_peak']:.2f} dBTP"
        )

    print("=" * 64)
    print()

    # ----------------------------------------------------------
    # CSV
    # ----------------------------------------------------------

    csv_file = out_folder / "normalization_report.csv"

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        #
        # Metadata
        #

        f.write(
            f"# TargetMode,"
            f"{'AUTO' if auto_mode else 'FIXED'}\n"
        )

        f.write(
            f"# TargetLUFS,"
            f"{target_lufs:.3f}\n"
        )

        f.write(
            f"# TruePeakLimit,"
            f"{true_peak_limit:.3f}\n"
        )

        if auto_mode:

            f.write(
                f"# LimitingTrack,"
                f"{limiting_track}\n"
            )

        f.write("\n")

        fieldnames = [

            "File",

            "Duration",

            "SampleRate",

            "LUFS",

            "Threshold",

            "Blocks",

            "GatedBlocks",

            "TruePeak",

            "GainLUFS",

            "GainTP",

            "PredictedLUFS",

            "AppliedGain",

            "Reason",

            "TargetLUFS",

            "TargetMode",

        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        digits = len(str(len(files)))

        # ------------------------------------------------------
        # PASS 2 : NORMALIZE + WRITE
        # ------------------------------------------------------

        print("Applying gain adjustment...\n")

        for n, item in enumerate(
            analysis,
            start=1
        ):

            fn = item["file"]

            stats = item["stats"]

            gain = compute_gain(
                stats,
                target_lufs,
                true_peak_limit
            )

            predicted_lufs = (
                stats["lufs"]
                + gain["gain"]
            )

            reason = (
                "TruePeak"
                if gain["gain_tp"] < gain["gain_lufs"]
                else "Loudness"
            )

            print(

                f"({n:>{digits}}/{len(files)}) "

                f"{fn.name:35s}"

                f" {stats['lufs']:7.2f}"

                f" → {predicted_lufs:7.2f} LUFS"

                f"  TP {stats['true_peak']:6.2f}"

                f"  Gain {gain['gain']:+6.2f}"

                f"  [{reason}]"

            )

            #
            # Apply gain
            #

            y, fs = ffmpeg_read(fn)

            y *= db_to_gain(gain["gain"])

            outfile = out_folder / fn.name

            sf.write(outfile, y, fs)

            #
            # CSV row
            #

            writer.writerow({

                "File": fn.name,

                "Duration": round(
                    stats["duration"],
                    3
                ),

                "SampleRate": stats["sample_rate"],

                "LUFS": round(
                    stats["lufs"],
                    3
                ),

                "Threshold": round(
                    stats["threshold"],
                    3
                ),

                "Blocks": stats["blocks"],

                "GatedBlocks": stats["gated_blocks"],

                "TruePeak": round(
                    stats["true_peak"],
                    3
                ),

                "GainLUFS": round(
                    gain["gain_lufs"],
                    3
                ),

                "GainTP": round(
                    gain["gain_tp"],
                    3
                ),

                "PredictedLUFS": round(
                    predicted_lufs,
                    3
                ),

                "AppliedGain": round(
                    gain["gain"],
                    3
                ),

                "Reason": reason,

                "TargetLUFS": round(
                    target_lufs,
                    3
                ),

                "TargetMode": (
                    "AUTO"
                    if auto_mode
                    else "FIXED"
                ),

            })

    print()
    print(f"Done. Files written to:\n{out_folder}")
    print(f"CSV report:\n{csv_file}")

