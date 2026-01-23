# Issue: Major - Test Reliability, Resource Management & Correctness 🛠️

**Problem:**
Several tests are triggering warnings and errors that compromise the validity of the test results and the stability of the test environment. These include unawaited coroutines, resource contamination across event loops, and potential logic errors in model loading.

## 1. Unawaited Coroutines (Silent Failures)
Asynchronous functions are being called without `await`, causing them to return a coroutine object instead of executing the intended logic. These tests "pass" despite potentially failing if actually run.
- `test/backends/test_ollama.py:187`: `coroutine 'MelleaSession.achat' was never awaited`
- `test/stdlib/requirements/test_reqlib_markdown.py`: `coroutine 'Requirement.validate' was never awaited` (lines 49, 53, 57)

## 2. Resource Contamination (Event Loop Errors)
`aiohttp` and other async resources are being closed on the wrong event loop, leading to `RuntimeError`.
- **Symptom**: `Task <Task pending ...> attached to a different loop`.
- **Source**: Likely unclosed `ClientSession` objects in `LiteLLM` or `Ollama` client tests.

## 3. Potential Correctness Issues (PEFT)
- `test/stdlib/components/intrinsic/test_rag.py`: `UserWarning: Already found a peft_config attribute in the model. This will lead to having multiple adapters in the model.`
- **Impact**: This suggests the test setup is incorrectly layering adapters or failing to clean up between runs, which could lead to non-deterministic/mismatched output evaluations.

**Action Items:**
- [ ] Audit and fix missing `await` calls.
- [ ] Implement robust cleanup for async clients (ensure `.close()` is called and awaited in fixtures).
- [ ] Investigate and fix PEFT adapter contamination in RAG tests.
- [ ] Verify that tests perform actual assertions once fixed.

**Priority:** High (Major)
**Note**: This excludes Watsonx-specific failures (`RateLimitError`) which are considered out-of-scope/unfixable given the environment limits.
