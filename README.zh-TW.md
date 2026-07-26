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
  輕量、跨供應商的 Python 模型價格套件。
</p>

<p align="center">
  <a href="README.md">English</a> |
  <strong>繁體中文</strong>
</p>

`Txaion Model Pricing` 是一個輕量的 Python 套件，用來查詢跨供應商模型
資訊，並依 token 數量計算 input、output 與 cached input 的美元成本。

本專案由 [Txaion](https://txaion.com) 開發與維護。

目前版本為 `0.1.1`，支援 Python 3.10 以上版本。

## 安裝

從 PyPI 安裝最新版本：

```bash
pip install txaion-model-pricing
```

若要進行本機開發，請 clone repository 後安裝開發依賴：

```bash
python -m pip install -e ".[dev]"
```

## 快速開始

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

所有成本均以 `decimal.Decimal` 回傳；套件不會自行四捨五入或轉換貨幣。

## 公開 API

### `count_models() -> int`

回傳快照中的模型數量。`sample_spec` 等資料格式描述不會被計入。

### `calculate_cost(model, tokens, token_type) -> Decimal`

依模型的每 token 價格計算美元成本：

- `input` 對應 `input_cost_per_token`
- `output` 對應 `output_cost_per_token`
- `cached` 對應 `cache_read_input_token_cost`

`tokens` 必須是非負整數。價格資料缺少指定欄位時，套件不會將成本視為零，
也不會退回其他價格。

除了三個簡稱外，`token_type` 也可以傳入模型快照實際包含的 scalar
per-token 原始價格欄位，例如 `input_cost_per_token_priority`、
`output_cost_per_reasoning_token` 或 `cache_creation_input_token_cost`。
即使欄位名稱含有 token 閾值，只要實際按 character、image、second、page、
request 或 session 計價，就不會被接受。

### `get_available_token_price_fields(model) -> tuple[str, ...]`

回傳該模型可用的 scalar per-token 原始價格欄位，結果排序固定。選擇非必要
或供應商特有欄位前，可先用此 API 查詢。

### `get_model_details(model) -> dict`

回傳模型資料的深層副本。修改回傳值不會污染套件內部快取。

## 錯誤處理

所有領域例外都繼承自 `ModelPriceError`：

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
    # 欄位名稱有效，但此模型沒有提供該價格。
    ...
except (InvalidTokenCountError, InvalidTokenTypeError):
    # token 數量或價格欄位名稱無效。
    ...
```

## 價格資料

內附資料是
[LiteLLM 模型價格與 context-window 資料](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)
的固定快照。來源 commit、擷取時間與 SHA-256 記錄在
`src/txaion_model_pricing/data_source.json`，第三方授權資訊請見
`THIRD_PARTY_NOTICES.md`。

維護者更新資料時必須指定固定 commit SHA 或 tag：

```bash
python scripts/update_prices.py <commit-or-tag>
```

更新工具會先下載及驗證 JSON，再原子替換資料與 metadata；`main`、`master`
及 `latest` 等浮動 ref 會被拒絕。

## 限制

- `0.1.1` 僅計算 scalar per-token 欄位的成本。
- 圖片、字元、秒數、頁數、request、session、搜尋、工具呼叫及儲存空間等
  非 token 單位計價尚未納入 `calculate_cost()`。若快照以 per-token 價格表示
  音訊內容，對應的 audio token 欄位仍可使用。
- 模型供應商可能隨時調整價格；本套件結果取決於內附快照，不保證與供應商
  當下價格一致。進行實際帳務或預算控管前，請核對供應商官方價格。

## 開發

```bash
ruff check .
pytest
python -m build
```

## 授權

本專案及 vendored LiteLLM 資料皆依 MIT License 再散布。詳細內容請見
`LICENSE` 與 `THIRD_PARTY_NOTICES.md`。
