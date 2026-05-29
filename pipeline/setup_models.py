"""Download the Kokoro v1.0 ONNX model + voices file into build/models/.

Idempotent: skips files that already exist. Run once before generating audio:
    .venv/bin/python -m pipeline.setup_models
"""

import urllib.request

from pipeline.config import KOKORO_MODEL, KOKORO_VOICES, MODEL_DIR

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
FILES = {
    KOKORO_MODEL: f"{BASE}/kokoro-v1.0.onnx",
    KOKORO_VOICES: f"{BASE}/voices-v1.0.bin",
}


def _download(url, dest):
    print(f"downloading {url}")

    def hook(block, bsize, total):
        if total > 0:
            pct = min(100, block * bsize * 100 // total)
            print(f"\r  {dest.name}: {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, hook)
    print()


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for dest, url in FILES.items():
        if dest.exists() and dest.stat().st_size > 0:
            print(f"ok {dest.name} ({dest.stat().st_size // 1024 // 1024} MB)")
            continue
        _download(url, dest)
        print(f"ok {dest.name} ({dest.stat().st_size // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
