# Resource Leaks in Test Suite 🔧

**Priority:** High

## Problem

Extensive `ResourceWarning` messages about unclosed sockets, transports, event loops, and HTTP client sessions throughout the test suite. While these occur in tests, they indicate improper cleanup patterns that could affect production code and may cause issues in long-running processes or when running tests in parallel.

**Note:** With 50+ resource warnings, new issues may get lost in the noise. Some async resource warnings can be challenging to fix, especially with third-party libraries. We may need to evaluate which are fixable vs. which should be suppressed.

## Warning Categories

### 1. Unclosed Sockets (20+ instances)
```
ResourceWarning: unclosed <socket.socket fd=X, family=2, type=1, proto=6, ...>
```

### 2. Unclosed Transports (30+ instances)
```
ResourceWarning: unclosed transport <_SelectorSocketTransport fd=X>
```

### 3. Unclosed Event Loops (1 instance)
```
ResourceWarning: unclosed event loop <_UnixSelectorEventLoop running=False closed=False debug=False>
```

### 4. Unclosed aiohttp Client Sessions
```
Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x...>
Unclosed connector
```

## Most Affected Tests

### High Impact (10+ warnings each)
- `test/backends/test_ollama.py::test_client_cache` - 10+ socket/transport warnings
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_basics` - 15+ warnings including event loop

### Medium Impact (5-10 warnings each)
- `test/backends/test_watsonx.py::test_client_cache` - 5+ socket/transport warnings
- `test/stdlib/test_session.py::test_start_session_watsonx` - 8+ socket/transport warnings
- `test/stdlib/test_chat_view.py::test_chat_view_simple_ctx` - Multiple socket warnings

### Low Impact (1-4 warnings each)
- `test/backends/test_openai_ollama.py::test_async_parallel_requests`
- `test/backends/test_ollama.py::test_generate_from_raw_with_format`
- `test/stdlib/sampling/test_majority_voting.py::test_majority_voting_for_math`
- `test/stdlib/test_functional.py::test_ainstruct`

## Possible Causes

- Backend HTTP clients not closed after tests
- `session.reset()` not closing all resources
- Event loops from `asyncio.run()` not cleaned up
- aiohttp sessions in LiteLLM backend not closed
- Test fixtures missing cleanup in try/finally blocks
