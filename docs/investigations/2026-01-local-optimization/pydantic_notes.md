# Investigation: Pydantic Input Support for Generative Slots

**Date**: 2026-01-14
**Status**: Implemented, Verified, then Reverted.
**Goal**: Allow passing `pydantic.BaseModel` objects directly to `@generative` functions as arguments.

## Context
Currently, Mellea's `@generative` decorator converts all arguments to strings using `str(val)`. For Pydantic models, this results in a Python-like representation (e.g., `User(name='Alice', age=30)`). The goal was to serialize them as standard JSON (e.g., `{"name": "Alice", "age": 30}`) to improve LLM comprehension.

## Implementation Details

We modified `mellea/stdlib/genslot.py` inside the `get_argument` function.

### Code Change
```python
# mellea/stdlib/genslot.py

def get_argument(key: str, val: Any, func: Callable) -> Argument:
    # ... existing processing ...

    # [NEW LOGIC START]
    if isinstance(val, BaseModel):
        # Serialize single Pydantic model to JSON string
        val = val.model_dump_json()
    elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], BaseModel):
        # Serialize list of Pydantic models as a JSON array string
        # Note: We manually construct the array to avoid overhead of a root model wrapper
        val = "[" + ",".join(v.model_dump_json() for v in val) + "]"
    # [NEW LOGIC END]
    
    elif param_type is str:
        val = f'"{val!s}"'

    return Argument(str(param_type), key, val)
```

## Verification Results

A regression test (`test/stdlib_basics/test_pydantic_input.py`) was created and verified against a local LMStudio instance (`granite-4.0-h-tiny-mlx`).

**Test Case `test_pydantic_serialization`**:
- **Input**: `User(name="Alice", age=30, bio="Loves AI")`
- **Expected Prompt Content**: `{"name":"Alice","age":30,"bio":"Loves AI"}`
- **Result**: PASSED. The LLM received valid JSON.

**Test Case `test_pydantic_list_serialization`**:
- **Input**: `[User(name="Alice"...), User(name="Bob"...)]`
- **Expected Prompt Content**: `[{"name":"Alice"...}, ...]`
- **Result**: PASSED.

## Reason for Revert
The user requested to "back off" the experiment but preserve the knowledge. This feature works technically but likely requires a broader design decision on whether Mellea should enforcing JSON serialization for *all* Pydantic objects or if it should be configurable.

## Future Recommendations
If this is reintroduced:
1.  Consider adding a configuration flag (globally or per-slot) to toggle this behavior.
2.  Ensure `pydantic` is strictly versioned if `model_dump_json` (Pydantic v2) is relied upon.
3.  Evaluate if `json.dumps(val.dict())` is needed for legacy Pydantic v1 support.
