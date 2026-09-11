import asyncio

from engines import advisor


def test_advisor_uses_configured_gemini_provider(monkeypatch):
    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return {"candidates": [{"content": {"parts": [{"text": "Which constraint would you test first?"}]}}]}
    captured = {}
    def fake_post(url, headers, timeout, json):
        captured.update({"url": url, "headers": headers, "payload": json})
        return FakeResponse()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_ADVISOR_MODEL", "gemini-test")
    monkeypatch.setattr(advisor.httpx, "post", fake_post)

    async def collect(): return "".join([part async for part in advisor.generate_advisor_stream("Help", "public context", "Socratic")])
    assert "constraint" in asyncio.run(collect())
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert "public context" in str(captured["payload"])


def test_advisor_uses_local_fallback_without_provider_configuration(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("GEMINI_ADVISOR_MODEL", raising=False)
    async def collect(): return "".join([part async for part in advisor.generate_advisor_stream("What about tariffs?", "", "")])
    assert "tariffs" in asyncio.run(collect()).lower()
