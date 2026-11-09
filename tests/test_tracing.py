"""A turn's trace: one AGENT span with a CHAT_MODEL span per step and a TOOL span per call."""

import json
from types import SimpleNamespace

import mlflow
from mlflow.entities import SpanType

from coati_agent.agent import Agent
from coati_agent.llm import OpenAICompatibleModel
from coati_agent.tools import ToolResult


def completion(content="", tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    usage = SimpleNamespace(prompt_tokens=12, completion_tokens=3)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def tool_call(call_id, name, **args):
    return SimpleNamespace(
        id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(args))
    )


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request):
        self.requests.append(request)
        return self.responses.pop(0)


def test_adapter_sends_the_system_prompt_first_and_parses_tool_calls():
    client = FakeClient(completion(tool_calls=[tool_call("c1", "search_docs", query="SSO")]))
    model = OpenAICompatibleModel(client, endpoint="databricks-test")

    reply = model.chat("rules", [{"role": "user", "content": "hi"}], tools=[{"type": "function"}])

    request = client.requests[0]
    assert request["model"] == "databricks-test"
    assert request["messages"][0] == {"role": "system", "content": "rules"}
    assert reply.tool_calls[0].name == "search_docs"
    assert json.loads(reply.tool_calls[0].arguments) == {"query": "SSO"}
    assert (reply.usage.input_tokens, reply.usage.output_tokens) == (12, 3)


def test_a_turn_records_agent_chat_and_tool_spans():
    client = FakeClient(
        completion(tool_calls=[tool_call("c1", "search_docs", query="SSO")]),
        completion(content="Enterprise."),
    )
    agent = Agent(
        model=OpenAICompatibleModel(client, endpoint="databricks-test"),
        system="rules",
        tool_specs=[],
        tools={"search_docs": lambda query: ToolResult(content="Enterprise has SSO.")},
    )

    agent.run([{"role": "user", "content": "Which plan has SSO?"}])

    trace = mlflow.get_trace(mlflow.get_last_active_trace_id())
    types = [(s.name, s.span_type) for s in trace.data.spans]
    assert types[0] == ("coati_agent", SpanType.AGENT)
    assert [t for _, t in types[1:]] == [SpanType.CHAT_MODEL, SpanType.TOOL, SpanType.CHAT_MODEL]
    tool_span = trace.data.spans[2]
    assert tool_span.name == "search_docs"
    assert tool_span.outputs == {"content": "Enterprise has SSO."}
