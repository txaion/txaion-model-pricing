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

The current version is `0.1.1` and requires Python 3.10 or later.

## Installation

Install the latest release from PyPI:

```bash
pip install txaion-model-pricing
```

For local development, clone the repository and install it with the development
dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
from txaion_model_pricing import (
    calculate_cost,
    count_models,
    get_available_token_price_fields,
    get_model_details,
)

print(count_models())

input_cost = calculate_cost("gpt-4o", 1_000_000, "input")
output_cost = calculate_cost("gpt-4o", 1_000_000, "output")
cached_cost = calculate_cost("gpt-4o", 1_000_000, "cached")
priority_cost = calculate_cost(
    "azure_ai/gpt-5.5",
    1_000_000,
    "input_cost_per_token_priority",
)

print(input_cost)   # Decimal("2.5000000")
print(output_cost)  # Decimal("10.00000")
print(cached_cost)  # Decimal("1.25000000")
print(priority_cost)  # Decimal("10.00000")

details = get_model_details("gpt-4o")
print(details["max_input_tokens"])

fields = get_available_token_price_fields("azure_ai/gpt-5.5")
print("input_cost_per_token_priority" in fields)  # True
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

In addition to the three aliases, `token_type` may be a raw scalar per-token
price field present in the model snapshot, such as
`input_cost_per_token_priority`, `output_cost_per_reasoning_token`, or
`cache_creation_input_token_cost`. Fields priced per character, image, second,
page, request, or session are not accepted, even when their names mention a
token threshold.

### `get_available_token_price_fields(model) -> tuple[str, ...]`

Returns a stable, sorted tuple of the raw scalar per-token price fields
available for the model. Use this discovery API before selecting optional or
provider-specific pricing fields.

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
    # The field name is valid, but this model does not provide that price.
    ...
except (InvalidTokenCountError, InvalidTokenTypeError):
    # The token count or price-field name is invalid.
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

- Version `0.1.1` only calculates costs from scalar per-token fields.
- Image-, character-, second-, page-, request-, session-, search-, tool-call-,
  and storage-based pricing are not supported by `calculate_cost()`. Token
  fields for audio content are supported when the snapshot expresses their
  unit as a per-token price.
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
