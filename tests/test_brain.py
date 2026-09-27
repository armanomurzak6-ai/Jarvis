from types import SimpleNamespace as NS

from jarvis.brain import ClaudeBrain
from jarvis.config import load_config
from jarvis.tools import ToolContext, default_registry


def text(t):
    return NS(type="text", text=t)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.beta = NS(messages=NS(create=self.create))

    def create(self, **kwargs):
        self.calls.append([dict(m) for m in kwargs["messages"]])
        return self.responses.pop(0)


def make(tmp_path, responses):
    cfg = load_config(env_file=tmp_path / "none.env")
    client = FakeClient(responses)
    ctx = ToolContext(config=cfg, confirm=lambda q: True)
    return ClaudeBrain(cfg, default_registry(), client=client), client, ctx


def test_tool_loop(tmp_path):
    tool_call = NS(type="tool_use", id="t1", name="get_datetime", input={})
    brain, client, ctx = make(tmp_path, [
        NS(stop_reason="tool_use", content=[tool_call], usage=None),
        NS(stop_reason="end_turn", content=[text("Сейчас полдень, сэр.")], usage=None),
    ])
    assert brain.respond("который час", ctx) == "Сейчас полдень, сэр."
    result = client.calls[1][-1]["content"][0]
    assert result["tool_use_id"] == "t1" and not result["is_error"]


def test_refusal_rolls_back(tmp_path):
    brain, client, ctx = make(tmp_path, [
        NS(stop_reason="refusal", content=[], usage=None),
        NS(stop_reason="end_turn", content=[text("Ок")], usage=None),
    ])
    assert "не могу" in brain.respond("плохое", ctx)
    assert brain.respond("привет", ctx) == "Ок"
    assert client.calls[1] == [{"role": "user", "content": "привет"}]
