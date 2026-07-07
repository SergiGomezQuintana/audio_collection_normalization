from pathlib import Path
import shutil
import subprocess

APP_NAME = "AudioCollectionNormalizer"


def clean(root: Path):
    shutil.rmtree(root / "build", ignore_errors=True)


def build(root: Path):
    entry = root / "src" / "main.py"
    output = root / "windows"

    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--clean",
        "--name", APP_NAME,
        "--distpath", str(output),
        "--workpath", str(root / "build"),
        "--specpath", str(root),
        str(entry),
    ], check=True)


def main():
    root = Path(__file__).resolve().parent.parent

    clean(root)
    build(root)

    print(f"\nDone!")
    print(f"Executable: {root / 'windows' / (APP_NAME + '.exe')}")


if __name__ == "__main__":
    main()