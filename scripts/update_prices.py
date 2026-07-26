"""下載並驗證指定 LiteLLM ref 的模型價格快照。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPOSITORY = "https://github.com/BerriAI/litellm"
UPSTREAM_FILE = "model_prices_and_context_window.json"
RAW_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/{ref}/"
    "model_prices_and_context_window.json"
)
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
MOVING_REFS = frozenset({"main", "master", "latest", "head"})

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src" / "txaion_model_pricing"
PRICES_PATH = PACKAGE_DIR / UPSTREAM_FILE
METADATA_PATH = PACKAGE_DIR / "data_source.json"


def _validated_ref(value: str) -> str:
    """拒絕浮動 branch 與不安全的 ref 字串。"""
    if value.lower() in MOVING_REFS:
        raise argparse.ArgumentTypeError(
            "ref 必須是固定 commit SHA 或 tag, 不可使用浮動 branch"
        )
    if not REF_PATTERN.fullmatch(value) or ".." in value:
        raise argparse.ArgumentTypeError("ref 格式無效")
    return value


def _download(ref: str) -> bytes:
    """下載指定 ref, 並限制最大回應大小。"""
    url = RAW_URL.format(ref=quote(ref, safe="/"))
    request = Request(url, headers={"User-Agent": "txaion-model-pricing-updater/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("上游價格檔案超過 10 MiB 限制")
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"無法下載 LiteLLM 價格資料: {exc}") from exc

    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise RuntimeError("上游價格檔案超過 10 MiB 限制")
    return payload


def _validate(payload: bytes) -> None:
    """確認下載內容符合本套件使用的基本資料契約。"""
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("上游回應不是有效 UTF-8 JSON") from exc

    if not isinstance(data, dict) or len(data) < 100:
        raise RuntimeError("上游價格資料必須是包含模型項目的 JSON object")
    if not isinstance(data.get("sample_spec"), dict):
        raise RuntimeError("上游價格資料缺少 sample_spec")
    if any(not isinstance(key, str) or not isinstance(value, dict)
           for key, value in data.items()):
        raise RuntimeError("上游價格資料包含無效模型項目")


def _atomic_write(path: Path, content: bytes) -> None:
    """在目標目錄建立暫存檔後, 以 os.replace 原子替換。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def update(ref: str) -> None:
    """下載、驗證並更新價格資料及來源 metadata。"""
    payload = _download(ref)
    _validate(payload)
    digest = hashlib.sha256(payload).hexdigest()
    metadata = {
        "source": "LiteLLM model price and context-window data",
        "repository": REPOSITORY,
        "upstream_file": UPSTREAM_FILE,
        "upstream_ref": ref,
        "retrieved_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "sha256": digest,
    }

    _atomic_write(PRICES_PATH, payload)
    _atomic_write(
        METADATA_PATH,
        (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode(),
    )
    print(f"Updated {PRICES_PATH.relative_to(ROOT)}")
    print(f"ref={ref}")
    print(f"sha256={digest}")


def main() -> None:
    """命令列進入點。"""
    parser = argparse.ArgumentParser(
        description="更新 vendored LiteLLM 模型價格快照"
    )
    parser.add_argument("ref", type=_validated_ref, help="固定 commit SHA 或 tag")
    arguments = parser.parse_args()
    update(arguments.ref)


if __name__ == "__main__":
    main()
