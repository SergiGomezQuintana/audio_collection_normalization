from pathlib import Path
import shutil
import subprocess
import sys

APP_NAME = "AudioCollectionNormalizer"


def clean(root: Path):
    shutil.rmtree(root / "build", ignore_errors=True)


def build(root: Path):

    entry = root / "src" / "gui.pyw"
    output = root / "macos"

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

        "--name", APP_NAME,

        "--distpath", str(output),
        "--workpath", str(root / "build"),
        "--specpath", str(root),

        str(entry),

    ], check=True)

    app = (
        root
        / "macos"
        / f"{APP_NAME}.app"
    )

    target = (
        app
        / "Contents"
        / "MacOS"
    )

    shutil.copy2(
        root / "third_party" / "macos" / "ffmpeg",
        target / "ffmpeg",
    )


def main():

    root = Path(__file__).resolve().parent.parent

    clean(root)

    build(root)

    app = (
        root
        / "macos"
        / f"{APP_NAME}.app"
    )

    print("\nDone!")
    print(f"Application: {app}")


if __name__ == "__main__":
    main()