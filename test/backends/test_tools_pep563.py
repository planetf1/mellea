# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for postponed-annotation (PEP 563) handling in
`convert_function_to_ollama_tool`.
"""

from mellea.backends.tools import convert_function_to_ollama_tool
from test.backends._pep563_tool_fixtures import Address, send_letter


def test_convert_function_to_ollama_tool_resolves_postponed_annotations():
    # Regression test: under `from __future__ import annotations`, a
    # non-builtin parameter type's annotation is a string rather than the
    # real type object, which Pydantic cannot resolve when building the
    # dynamic schema model — raising PydanticUserError instead of producing
    # a tool schema.

    # Guard the precondition: if the fixture module ever drops its
    # `from __future__ import annotations`, this test would otherwise keep
    # passing without exercising postponed annotations at all.
    assert send_letter.__annotations__["to"] == "Address"

    tool = convert_function_to_ollama_tool(send_letter)
    assert tool.function is not None
    assert tool.function.parameters is not None

    props = tool.function.parameters.model_dump(exclude_none=True)["properties"]
    assert props["to"]["type"] == "object"
    assert props["to"]["title"] == Address.__name__
    assert props["to"]["properties"]["city"]["type"] == "string"
