"""價格快照更新工具的離線測試。"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


def _load_update_script() -> ModuleType:
    script_path = Path(__file__).parents[1] / "scripts" / "update_prices.py"
    spec = importlib.util.spec_from_file_location("update_prices", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/update_prices.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


update_prices = _load_update_script()


@pytest.mark.parametrize("ref", ["main", "master", "latest", "HEAD"])
def test_moving_refs_are_rejected(ref: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        update_prices._validated_ref(ref)


@pytest.mark.parametrize(
    "ref",
    [
        "ae81625ee6659c96abf87e84e74840f9c0b3164a",
        "v1.2.3",
        "release/2026-07",
    ],
)
def test_fixed_refs_are_accepted(ref: str) -> None:
    assert update_prices._validated_ref(ref) == ref


def test_invalid_snapshot_is_rejected() -> None:
    data = {f"model-{index}": {} for index in range(100)}

    with pytest.raises(RuntimeError, match="sample_spec"):
        update_prices._validate(json.dumps(data).encode())


def test_valid_snapshot_shape_is_accepted() -> None:
    data = {"sample_spec": {}}
    data.update({f"model-{index}": {} for index in range(100)})

    update_prices._validate(json.dumps(data).encode())


def test_atomic_write_replaces_target(tmp_path) -> None:
    target = tmp_path / "prices.json"
    target.write_bytes(b"old")

    update_prices._atomic_write(target, b"new")

    assert target.read_bytes() == b"new"
    assert not list(tmp_path.glob("*.tmp"))
