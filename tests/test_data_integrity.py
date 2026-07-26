"""Vendored 價格資料與來源 metadata 的完整性測試。"""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files


def test_bundled_snapshot_matches_recorded_sha256() -> None:
    package = files("txaion_model_pricing")
    payload = package.joinpath("model_prices_and_context_window.json").read_bytes()
    metadata = json.loads(package.joinpath("data_source.json").read_bytes())

    assert metadata["upstream_ref"] not in {"main", "master", "latest", "head"}
    assert metadata["sha256"] == hashlib.sha256(payload).hexdigest()


def test_bundled_snapshot_has_expected_shape() -> None:
    payload = (
        files("txaion_model_pricing")
        .joinpath("model_prices_and_context_window.json")
        .read_bytes()
    )
    data = json.loads(payload)

    assert len(data) > 100
    assert isinstance(data["sample_spec"], dict)
    assert all(isinstance(key, str) for key in data)
    assert all(isinstance(value, dict) for value in data.values())
