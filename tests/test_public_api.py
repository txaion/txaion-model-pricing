"""套件頂層公開契約測試。"""

from __future__ import annotations

import txaion_model_pricing


def test_version_and_public_exports() -> None:
    assert txaion_model_pricing.__version__ == "0.1.0"
    assert set(txaion_model_pricing.__all__) == {
        "InvalidTokenCountError",
        "InvalidTokenTypeError",
        "ModelPriceError",
        "NotFound",
        "PriceUnavailableError",
        "TokenType",
        "__version__",
        "calculate_cost",
        "count_models",
        "get_model_details",
    }
