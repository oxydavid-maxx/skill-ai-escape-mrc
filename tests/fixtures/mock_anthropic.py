"""Deterministic mock for Anthropic API used in tests."""


def make_call_claude_mock(responses: dict):
    """Return a call_claude replacement that dispatches by system-prompt substring.

    `responses` keys are substrings of system prompt; values are the returned object
    (str for text, dict/list for parse_json=True).
    """

    def mock_call(model, system, user, parse_json=False, max_tokens=None, temperature=None):
        for key, value in responses.items():
            if key in system:
                return value
        raise KeyError(f"No mock response matches system prefix: {system[:50]}")

    return mock_call


def make_websearch_mock(results_by_query: dict | None = None):
    """Return a websearch replacement. If results_by_query provided, dispatch
    by substring match; otherwise return a generic result."""

    def mock_search(query, max_tokens=None):
        content = "generic search result"
        if results_by_query:
            for key, val in results_by_query.items():
                if key in query:
                    content = val
                    break
        return {"query": query, "results": content, "timestamp": 0.0}

    return mock_search
