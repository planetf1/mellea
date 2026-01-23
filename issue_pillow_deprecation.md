# Pillow Image Mode Parameter Deprecation ⚠️

## Problem

Vision tests trigger deprecation warnings in Pillow 11.3.0 (current version).

**Warning:**
```
DeprecationWarning: 'mode' parameter is deprecated and will be removed in Pillow 13 (2026-10-15)
  random_image = Image.fromarray(random_pixel_data, "RGB")
```

## Affected Tests

- `test/backends/test_vision_ollama.py:38`
- `test/backends/test_vision_openai.py:48`

Both in the `pil_image` fixture.

## Background

The `mode` parameter in `Image.fromarray()` was fully deprecated in Pillow 11.3.0. However, this was **partially reverted in Pillow 12.0.0** - the parameter is now only deprecated when changing data types (e.g., reading RGB as YCbCr).

Our usage passes RGB data with `"RGB"` mode - this is **not** changing data types, so it's no longer deprecated in Pillow 12.0.0+.

## Solution

**Upgrade Pillow to 12.0.0 or later** - this will eliminate the warning without code changes.

```bash
uv pip install --upgrade pillow
```

Our usage will be valid in Pillow 12.0.0+ since we're not changing data types.

## Action Items

- [ ] Upgrade Pillow to version 12.0.0 or later
- [ ] Run affected tests to verify warnings are gone

## Verification

```bash
# Check current version
uv pip list | grep pillow

# Upgrade
uv pip install --upgrade pillow

# Verify warnings are gone
uv run pytest test/backends/test_vision_ollama.py test/backends/test_vision_openai.py -v -W error::DeprecationWarning
```

## References

- [Pillow Deprecations](https://pillow.readthedocs.io/en/stable/deprecations.html#image-fromarray-mode-parameter)
- [Image.fromarray() docs](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.fromarray)