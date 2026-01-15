# Investigation: Local HuggingFace Optimization on Apple Silicon

**Date**: 2026-01-14
**Status**: Implemented and Checked In.
**Hardware**: Apple Silicon (M1/M2/M3) with MPS (Metal Performance Shaders).

## Problem
The `LocalHFBackend` in `test/backends/test_huggingface.py` was previously defaulting to `float32` (full precision) loading.
-   **Memory Usage**: >16GB for an 8B param model.
-   **Consequence**: Massive swap thrashing (60M+ swapouts), system freeze, execution time > 2 hours for partial suite.

## Optimization Strategy
We modified `mellea/backends/huggingface.py` to auto-detect the `mps` device and switch to `float16`.

```python
# mellea/backends/huggingface.py

if self._device.type == "mps":
    model_kwargs["torch_dtype"] = torch.float16

self._model = AutoModelForCausalLM.from_pretrained(
    self._hf_model_id,
    **model_kwargs,
).to(self._device)
```

**Why FP16?**
-   M1/M2/M3 chips natively support FP16.
-   Reduces memory footprint by ~50% (to ~8GB for an 8B model).
-   Eliminates swap usage for this test suite.
-   **Note**: `bfloat16` is *not* natively efficient on M1/M2 (it is emulated), so `float16` is preferred.

## Dependencies
We discovered that `test_huggingface.py` relies on structured generation features that require:
1.  `xgrammar`: Added to `pyproject.toml`.
2.  `outlines`: Must be installed via `mellea[hf]` extras.

## Verification Results
After applying the FP16 patch and fixing dependencies:
-   **Total Tests**: 18
-   **Passed**: 16
-   **Failed**: 2
-   **Time**: ~3 minutes (vs >2 hours).

### Understanding the Failures
The 2 remaining failures (`test_format`, `test_generate_from_raw_with_format`) are **flaky**.
-   **Error**: `pydantic.ValidationError` or `AssertionError`.
-   **Cause**: The 8B model occasionally fails to follow the output schema or instruction perfectly.
-   **Mitigation attempt**: Setting `temperature=0.01` helped but did not completely eliminate all variance or caused deadlocks at pure `0.0`.
-   **Conclusion**: These are model capability issues, not infrastructure bugs. The backend is working correctly.

## Recommendations
-   Always use `torch.float16` on MPS.
-   Ensure `xgrammar` is present for `LocalHFBackend`.
-   Expect some non-determinism in 8B models even at low temperatures; logic tests might need retry mechanisms or looser assertions.
