# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 16:02:39 2026

@author: sergi
"""

import argparse
from BS1770_normalize import normalize_folder
from pathlib import Path

if __name__ == "__main__":

    

    parser = argparse.ArgumentParser(
        description="Normalize a folder of MP3 files using A-weighted loudness normalization."
    )

    parser.add_argument(
        "in_folder",
        help="Input folder containing MP3 files"
    )

    parser.add_argument(
        "out_folder",
        nargs="?",
        default=None,
        help="Output folder for normalized MP3 files (default: <input>/norm)"
    )
    
    parser.add_argument(
        "--target-lufs",
        default="auto",
        help=(
            "Target integrated loudness in LUFS. "
            "Use a numeric value (e.g. -18) or 'auto' "
            "(default: auto)."
        )
    )
    
    parser.add_argument(
        "--true-peak_limit",
        type=float,
        default=-1.0,
        help="Target A-weighted crest level in dB (default: -9.0)"
    )

    args = parser.parse_args()
    
    if args.out_folder is None:
        args.out_folder = str(Path(args.in_folder) / "norm")
    #
    # Parse target_lufs
    #
    
    if args.target_lufs.lower() != "auto":
    
        try:
            args.target_lufs = float(args.target_lufs)
    
        except ValueError:
    
            parser.error(
                "--target_lufs must be a number or 'auto'"
            )

    normalize_folder(
        in_folder=args.in_folder,
        out_folder=args.out_folder,
        target_lufs=args.target_lufs,
        true_peak_limit=args.true_peak_limit,
    )