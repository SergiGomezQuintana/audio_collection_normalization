from pathlib import Path
import shutil
import subprocess
import sys

APP_NAME = "AudioCollectionNormalizer"


def clean(root: Path):
    shutil.rmtree(root / "build", ignore_errors=True)


def build(root: Path):

    entry = root / "src" / "gui.pyw"
    output = root / "windows"

    print("Python:", sys.executable)
    print("Root:", root)
    print("Entry exists:", entry.exists())
    print("Entry:", entry)
    print("Output:", output)

    subprocess.run([
        sys.executable,
        "-m",
        "PyInstaller",

        "--onedir",
        "--windowed",
        "--clean",

        "--name",
        APP_NAME,

        "--distpath",
        str(output),

        "--workpath",
        str(root / "build"),

        "--specpath",
        str(root),

        str(entry),

    ], check=True)

    dist = (
        root
        / "windows"
        / APP_NAME
    )

    ffmpeg = root / "third_party" / "windows" / "ffmpeg.exe"

    if not ffmpeg.exists():
        raise RuntimeError(
            f"Missing ffmpeg:\n{ffmpeg}"
        )

    shutil.copy2(
        ffmpeg,
        dist / "ffmpeg.exe",
    )
    

def main():

    root = Path(__file__).resolve().parent.parent

    clean(root)

    build(root)

    print("\nDone!")
    print(
        f"Executable: {root / 'windows' / (APP_NAME + '.exe')}"
    )


if __name__ == "__main__":
    main()