<p align="center">
  <a href="https://txaion.com">
    <img
      src="https://static.txaion.com/product/model-price/model-price-tp.png"
      alt="Txaion"
      width="360"
    >
  </a>
</p>

<h1 align="center">Txaion Model Pricing</h1>

<p align="center">
  Lightweight, cross-provider model pricing for Python.
</p>

<p align="center">
  <strong>English</strong> |
  <a href="README.zh-TW.md">繁體中文</a>
</p>

`Txaion Model Pricing` is a lightweight Python package for querying
cross-provider model information and calculating USD costs for input, output,
and cached-input tokens.

Developed and maintained by [Txaion](https://txaion.com).

The current version is `0.1.0` and requires Python 3.10 or later.

## Installation

Install the package from the project directory:

```bash
python -m pip install .
```

Install the development dependencies for testing and building:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
from txaion_model_pricing import calculate_cost, count_models, get_model_details

print(count_models())

input_cost = calculate_cost("gpt-4o", 1_000_000, "input")
output_cost = calculate_cost("gpt-4o", 1_000_000, "output")
cached_cost = calculate_cost("gpt-4o", 1_000_000, "cached")

print(input_cost)   # Decimal("2.5000000")
print(output_cost)  # Decimal("10.00000")
print(cached_cost)  # Decimal("1.25000000")

details = get_model_details("gpt-4o")
print(details["max_input_tokens"])
```

All costs are returned as `decimal.Decimal` values. The package does not round
results or perform currency conversion.

## Public API

### `count_models() -> int`

Returns the number of models in the bundled snapshot. Metadata entries such as
`sample_spec` are excluded.

### `calculate_cost(model, tokens, token_type) -> Decimal`

Calculates the USD cost using the model's per-token price:

- `input` maps to `input_cost_per_token`
- `output` maps to `output_cost_per_token`
- `cached` maps to `cache_read_input_token_cost`

`tokens` must be a non-negative integer. If the requested price field is
unavailable, the package does not treat the cost as zero or fall back to a
different price.

### `get_model_details(model) -> dict`

Returns a deep copy of the model data. Modifying the returned value does not
affect the package's internal cache.

## Error handling

All domain-specific exceptions inherit from `ModelPriceError`:

```python
from txaion_model_pricing import (
    InvalidTokenCountError,
    InvalidTokenTypeError,
    NotFound,
    PriceUnavailableError,
    calculate_cost,
)

try:
    cost = calculate_cost("unknown-model", 1_000, "input")
except NotFound:
    ...
except PriceUnavailableError:
    ...
except (InvalidTokenCountError, InvalidTokenTypeError):
    ...
```

## Price data

The package includes a pinned snapshot of the
[LiteLLM model price and context-window data](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json).
The source commit, retrieval time, and SHA-256 checksum are recorded in
`src/txaion_model_pricing/data_source.json`. See `THIRD_PARTY_NOTICES.md` for
third-party attribution and licensing information.

Maintainers must specify an immutable commit SHA or tag when updating the
snapshot:

```bash
python scripts/update_prices.py <commit-or-tag>
```

The update tool downloads and validates the JSON before atomically replacing
the snapshot and its metadata. Moving refs such as `main`, `master`, and
`latest` are rejected.

## Limitations

- Version `0.1.0` only calculates token-based input, output, and cached-input
  costs.
- Image, audio, search, tool-call, session, and storage pricing are not
  supported by `calculate_cost()`.
- Model providers may change their prices at any time. Results depend on the
  bundled snapshot and may not match current provider pricing. Verify official
  provider prices before using the results for billing or budget enforcement.

## Development

```bash
ruff check .
pytest
python -m build
```

## License

This project and the vendored LiteLLM data are redistributed under the MIT
License. See `LICENSE` and `THIRD_PARTY_NOTICES.md` for details.
