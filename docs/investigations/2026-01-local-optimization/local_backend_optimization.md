# Research Report: Local Backend Optimization (MPS/FP16)
**Date**: 2026-01-14
**Topic**: Stabilizing HuggingFace Backend on Apple Silicon

## 1. The Challenge
Running `LocalHFBackend` with 7B+ parameter models (e.g., Llama-3-8B) on Apple Silicon (M1/M2/M3) was causing system instability.
*   **Symptoms**: Swap usage >20GB, System freezes, Execution time >2 hours.
*   **Root Cause**: `AutoModel` defaults to `float32` (Full Precision) unless specified. This balloons an 8B model to ~32GB VRAM, exceeding the unified memory budget of standard MacBooks (16/24GB).

## 2. The Solution: FP16 Detection
We implemented automatic `float16` casting when the `mps` device is detected.

### Implementation Details
In `mellea/backends/huggingface.py`:
```python
if self._device.type == "mps":
    # M-series chips support native FP16 but have issues with BFloat16 emulation.
    model_kwargs["torch_dtype"] = torch.float16
```

### performance Impact
*   **Memory**: Reduced from ~32GB to ~14GB (Fits in 16GB Unified Memory).
*   **Speed**: Inference time for test suite dropped from >2 hours (thrashing) to ~3 minutes.
*   **Quality**: No degradation in test pass rate compared to CPU execution.

## 3. Dependency Findings (xgrammar)
We discovered that `LocalHFBackend` has a hard dependency on `xgrammar` (via `outlines`) for constrained generation.
*   **Issue**: `pip install mellea` did not originally include `xgrammar`, causing `ImportError` in local tests.
*   **Fix**: Added `xgrammar` to `pyproject.toml`.
*   **Note**: `outlines` (Rust dependency) has compilation issues on Python 3.13. We recommend Python 3.12 for local development.

## 4. Temperature Sensitivity
We found that 8B models are highly sensitive to temperature at low precision.
*   `temperature=0.0`: Caused livelocks (infinite loops) in some `outlines` samplers.
*   `temperature=0.01`: Provided the best balance of determinism and liveness.
