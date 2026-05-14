from __future__ import annotations

import httpx

from memory_stack.cfg import Settings
from memory_stack.llm.client import ConfiguredLLMClient, openai_response_text


def test_configured_openai_llm_client_posts_json_schema(monkeypatch) -> None:
    captured = {}
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["Authorization"]
        captured["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"ok": true}',
                            }
                        ]
                    }
                ]
            },
        )

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda timeout: real_client(transport=httpx.MockTransport(handler), timeout=timeout),
    )
    settings = Settings(
        brain_llm_enabled=True,
        openai_api_key="sk-test",
        openai_auth_mode="api_key",
    )

    result = ConfiguredLLMClient(settings).complete_json(
        "prompt",
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}},
        },
    )

    assert result == {"ok": True}
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["auth"] == "Bearer sk-test"
    assert '"type":"json_schema"' in captured["json"].replace(" ", "")


def test_openai_response_text_accepts_output_text_shortcut() -> None:
    assert openai_response_text({"output_text": '{"ok": true}'}) == '{"ok": true}'


def test_configured_openai_llm_client_uses_oauth_codex_backend(monkeypatch, tmp_path) -> None:
    captured = {}

    def fake_create_structured_output(self, **kwargs):
        captured["settings"] = self.settings
        captured["kwargs"] = kwargs
        return '{"ok": true}'

    monkeypatch.setattr(
        "memory_stack.llm.client.CogneeOAuthLLMAdapter.create_structured_output",
        fake_create_structured_output,
    )
    settings = Settings(
        brain_llm_enabled=True,
        openai_auth_mode="oauth",
        openai_api_key=None,
        llm_api_key=None,
        brain_provider_auth_profiles_path=str(tmp_path / "profiles.json"),
        brain_provider_auth_state_dir=str(tmp_path / "state"),
    )
    assert settings.openai_auth_mode == "oauth"

    result = ConfiguredLLMClient(settings).complete_json(
        "prompt",
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}},
        },
        tools=[{"type": "web_search"}],
        tool_choice="auto",
    )

    assert result == {"ok": True}
    assert captured["settings"] is settings
    assert captured["kwargs"]["response_model"] is str
    assert captured["kwargs"]["tools"] == [{"type": "web_search"}]
    assert captured["kwargs"]["tool_choice"] == "auto"
    assert "JSON schema:" in captured["kwargs"]["text_input"]
