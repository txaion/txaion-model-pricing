"""模型價格查詢與 token 成本計算。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from threading import RLock
from types import MappingProxyType
from typing import Literal, TypeAlias

import orjson

TokenType: TypeAlias = Literal["input", "output", "cached"]

_PRICE_FIELDS: Mapping[TokenType, str] = MappingProxyType(
    {
        "input": "input_cost_per_token",
        "output": "output_cost_per_token",
        "cached": "cache_read_input_token_cost",
    }
)
_METADATA_KEYS = frozenset({"sample_spec"})
_PRICES_RESOURCE = "model_prices_and_context_window.json"
_PRICES: Mapping[str, Mapping[str, object]] | None = None
_PRICES_LOCK = RLock()


class ModelPriceError(Exception):
    """所有 Txaion Model Pricing 領域錯誤的基底類別。"""


class NotFound(ModelPriceError):
    """找不到指定模型。"""

    def __init__(self, model: str) -> None:
        super().__init__(f"Model price not found for model: {model}.")


class InvalidTokenTypeError(ModelPriceError):
    """token 類型不是 input、output 或 cached。"""

    def __init__(self, token_type: object) -> None:
        super().__init__(
            f"Invalid token type: {token_type!r}. "
            "Expected one of: input, output, cached."
        )


class InvalidTokenCountError(ModelPriceError):
    """token 數量不是非負整數。"""

    def __init__(self, tokens: object) -> None:
        super().__init__(
            f"Invalid token count: {tokens!r}. Expected a non-negative integer."
        )


class PriceUnavailableError(ModelPriceError):
    """模型存在, 但沒有指定 token 類型的價格。"""

    def __init__(self, model: str, token_type: TokenType) -> None:
        super().__init__(
            f"Price unavailable for model {model!r} and token type {token_type!r}."
        )


def _load_prices() -> Mapping[str, Mapping[str, object]]:
    """延遲載入價格資料, 並以唯讀 mapping 快取。"""
    global _PRICES

    if _PRICES is not None:
        return _PRICES

    with _PRICES_LOCK:
        if _PRICES is not None:
            return _PRICES

        raw_data = orjson.loads(
            files("txaion_model_pricing").joinpath(_PRICES_RESOURCE).read_bytes()
        )
        if not isinstance(raw_data, dict):
            raise ModelPriceError("The bundled model price data must be a JSON object.")

        prices: dict[str, Mapping[str, object]] = {}
        for model, details in raw_data.items():
            if model in _METADATA_KEYS:
                continue
            if not isinstance(model, str) or not isinstance(details, dict):
                raise ModelPriceError(
                    "The bundled model price data contains an invalid model entry."
                )
            prices[model] = MappingProxyType(details)

        _PRICES = MappingProxyType(prices)
        return _PRICES


def count_models() -> int:
    """回傳資料集中真正的模型數量, 不包含 schema 範例。"""
    return len(_load_prices())


def calculate_cost(
    model: str,
    tokens: int,
    token_type: TokenType | str,
) -> Decimal:
    """計算指定模型與 token 類型的美元成本。

    Args:
        model: 價格資料中的模型識別名稱。
        tokens: 非負整數 token 數量。
        token_type: ``input``、``output`` 或 ``cached``。

    Returns:
        未量化、未四捨五入的美元成本。

    Raises:
        InvalidTokenCountError: ``tokens`` 不是非負整數。
        InvalidTokenTypeError: ``token_type`` 不在支援範圍。
        NotFound: 找不到模型。
        PriceUnavailableError: 模型沒有指定類型的 token 價格。
    """
    if type(tokens) is not int or tokens < 0:
        raise InvalidTokenCountError(tokens)
    if token_type not in _PRICE_FIELDS:
        raise InvalidTokenTypeError(token_type)

    prices = _load_prices()
    if model not in prices:
        raise NotFound(model)

    price_field = _PRICE_FIELDS[token_type]
    price = prices[model].get(price_field)
    if price is None:
        raise PriceUnavailableError(model, token_type)

    try:
        return Decimal(str(price)) * tokens
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PriceUnavailableError(model, token_type) from exc


def get_model_details(model: str) -> dict[str, object]:
    """回傳指定模型資料的獨立深層副本。"""
    prices = _load_prices()
    if model not in prices:
        raise NotFound(model)
    return deepcopy(dict(prices[model]))
