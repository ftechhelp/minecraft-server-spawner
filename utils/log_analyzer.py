import json
import os
from urllib import error, parse, request


class GeminiError(Exception):
    pass


class LogAnalysisError(GeminiError):
    pass


def _gemini_generate(prompt: str, response_mime_type: str = None, temperature: float = 0.1) -> str:
    """Send a single-prompt request to Gemini and return the response text."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiError("Gemini is not configured. Set GEMINI_API_KEY to enable this feature.")
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview").strip() or "gemini-3.1-flash-lite-preview"

    generation_config = {"temperature": temperature}
    if response_mime_type:
        generation_config["responseMimeType"] = response_mime_type

    payload = {
        "generationConfig": generation_config,
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={parse.quote(api_key)}"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise GeminiError(f"Gemini request failed: {response_body}")
    except error.URLError as exc:
        raise GeminiError(f"Could not reach Gemini: {exc.reason}")

    try:
        payload = json.loads(body)
        candidate = payload["candidates"][0]
        parts = candidate["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GeminiError(f"Unexpected Gemini response format: {exc}")

    if not text:
        raise GeminiError("Gemini returned an empty response.")

    return text


def answer_docs_question(question: str, docs_text: str) -> str:
    prompt = (
        "You are the help assistant for a Minecraft server web panel. "
        "Answer the user's question using ONLY the documentation below. "
        "Be concise and practical; give step-by-step instructions when the documentation describes a procedure. "
        "If the documentation does not cover the question, say that plainly instead of guessing. "
        "Answer in plain text without markdown formatting.\n\n"
        "Documentation:\n"
        f"{docs_text}\n\n"
        "Question:\n"
        f"{question}"
    )
    return _gemini_generate(prompt, temperature=0.3)


class LogAnalyzer:
    def analyze(self, spawn) -> dict:
        logs = (spawn.get_logs() or "").strip()
        if not logs or logs == "No logs available.":
            raise LogAnalysisError("No logs are available to analyze for this spawn.")

        trimmed_logs = self._trim_logs(logs)
        try:
            text = _gemini_generate(self._build_prompt(spawn, trimmed_logs), response_mime_type="application/json")
        except LogAnalysisError:
            raise
        except GeminiError as exc:
            raise LogAnalysisError(str(exc))

        return self._parse_analysis(text)

    def _trim_logs(self, logs: str) -> str:
        lines = logs.splitlines()
        tail_lines = lines[-250:] if len(lines) > 250 else lines
        trimmed = "\n".join(tail_lines)
        if len(trimmed) > 30000:
            trimmed = trimmed[-30000:]
        return trimmed

    def _build_prompt(self, spawn, logs: str) -> str:
        return (
            "You are analyzing Minecraft server logs for operational health. "
            "Your job is to determine whether the logs indicate a real problem. "
            "If there is no clear issue, do not discuss log details and simply say everything looks normal. "
            "Respond with valid JSON only using this exact shape: "
            '{"outcome":"normal|problem","summary":"string","problem":"string","details":"string"}. '
            "Rules: "
            "1) outcome must be normal or problem. "
            "2) If outcome is normal, set summary to a short statement that everything looks normal, and set problem and details to empty strings. "
            "3) If outcome is problem, summary should be a short diagnosis, problem should name the issue, and details should be a brief plain-English explanation. "
            "4) Ignore harmless startup noise unless it indicates a real failure. "
            "5) Be concise.\n\n"
            f"Spawn name: {spawn.name}\n"
            f"Status: {spawn.get_status()}\n"
            f"Server type: {spawn.type}\n"
            f"Minecraft version: {spawn.minecraft_version}\n"
            f"Forge version: {spawn.forge_version}\n\n"
            "Recent logs:\n"
            f"{logs}"
        )

    def _parse_analysis(self, text: str) -> dict:
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            analysis = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LogAnalysisError(f"Gemini returned invalid JSON: {exc}")

        outcome = analysis.get("outcome", "").strip().lower()
        summary = analysis.get("summary", "").strip()
        problem = analysis.get("problem", "").strip()
        details = analysis.get("details", "").strip()

        if outcome not in {"normal", "problem"}:
            raise LogAnalysisError("Gemini returned an invalid outcome.")

        if outcome == "normal":
            if not summary:
                summary = "Everything looks normal."
            problem = ""
            details = ""

        if outcome == "problem" and not summary:
            summary = "A likely issue was found in the logs."

        return {
            "outcome": outcome,
            "summary": summary,
            "problem": problem,
            "details": details,
        }


log_analyzer = LogAnalyzer()
