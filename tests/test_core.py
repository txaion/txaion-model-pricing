"""核心公開 API 的行為測試。"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from importlib.resources import files

import pytest

import txaion_model_pricing.core as core
from txaion_model_pricing import (
    InvalidTokenCountError,
    InvalidTokenTypeError,
    NotFound,
    PriceUnavailableError,
    calculate_cost,
    count_models,
    get_model_details,
)


@pytest.mark.parametrize(
    ("token_type", "expected"),
    [
        ("input", Decimal("2.5")),
        ("output", Decimal("10")),
        ("cached", Decimal("1.25")),
    ],
)
def test_calculate_known_gpt_4o_cost(
    token_type: str,
    expected: Decimal,
) -> None:
    result = calculate_cost("gpt-4o", 1_000_000, token_type)

    assert isinstance(result, Decimal)
    assert result == expected


def test_zero_tokens_costs_zero() -> None:
    assert calculate_cost("gpt-4o", 0, "input") == Decimal(0)


@pytest.mark.parametrize("tokens", [-1, 1.5, True, "100", None])
def test_invalid_token_count_is_rejected(tokens: object) -> None:
    with pytest.raises(InvalidTokenCountError):
        calculate_cost("gpt-4o", tokens, "input")  # type: ignore[arg-type]


def test_invalid_token_type_uses_public_error() -> None:
    with pytest.raises(InvalidTokenTypeError):
        calculate_cost("gpt-4o", 100, "banana")


def test_unknown_model_uses_public_error() -> None:
    with pytest.raises(NotFound):
        calculate_cost("does-not-exist", 100, "input")


def test_missing_price_is_not_treated_as_zero() -> None:
    with pytest.raises(PriceUnavailableError):
        calculate_cost("256-x-256/dall-e-2", 1, "input")


def test_metadata_entry_is_not_a_model() -> None:
    with pytest.raises(NotFound):
        get_model_details("sample_spec")


def test_count_excludes_sample_spec() -> None:
    raw = json.loads(
        files("txaion_model_pricing")
        .joinpath("model_prices_and_context_window.json")
        .read_bytes()
    )

    assert count_models() == len(raw) - 1


def test_model_details_are_deeply_isolated() -> None:
    first = get_model_details("gpt-4.1")
    original_endpoints = list(first["supported_endpoints"])
    first["supported_endpoints"].append("/mutated")
    first["max_input_tokens"] = 1

    second = get_model_details("gpt-4.1")

    assert second["supported_endpoints"] == original_endpoints
    assert second["max_input_tokens"] != 1


def test_repeated_calls_return_consistent_results() -> None:
    expected = calculate_cost("gpt-4o", 123_456, "output")

    assert all(
        calculate_cost("gpt-4o", 123_456, "output") == expected
        for _ in range(10)
    )


def test_concurrent_first_access_loads_data_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_loads = core.orjson.loads
    calls = 0

    def counting_loads(payload: bytes) -> object:
        nonlocal calls
        calls += 1
        return original_loads(payload)

    monkeypatch.setattr(core, "_PRICES", None)
    monkeypatch.setattr(core.orjson, "loads", counting_loads)

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(lambda _: core.count_models(), range(32)))

    assert len(set(results)) == 1
    assert calls == 1
