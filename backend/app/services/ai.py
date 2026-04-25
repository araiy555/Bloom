"""Thin wrapper around OpenAI / Anthropic chat completions.

Falls back to a deterministic stub response when no API key is configured so the
MVP can still run end-to-end during local development.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from typing import Iterable

from app.core.config import get_settings

settings = get_settings()


def _stub_reply(messages: list[dict]) -> str:
    last = next((m for m in reversed(messages) if m["role"] == "user"), None)
    user_text = last["content"] if last else ""
    return (
        "[Bloom: APIキー未設定モード] "
        "実際のAI応答を得るには backend/.env に OPENAI_API_KEY または ANTHROPIC_API_KEY を設定してください。\n\n"
        f"あなたの入力: {user_text[:400]}"
    )


def chat(messages: list[dict], *, json_mode: bool = False) -> str:
    """messages: [{role, content}, ...]"""

    provider = settings.DEFAULT_PROVIDER

    if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        return _anthropic_chat(messages, json_mode=json_mode)
    if provider == "openai" and settings.OPENAI_API_KEY:
        return _openai_chat(messages, json_mode=json_mode)

    if settings.OPENAI_API_KEY:
        return _openai_chat(messages, json_mode=json_mode)
    if settings.ANTHROPIC_API_KEY:
        return _anthropic_chat(messages, json_mode=json_mode)

    return _stub_reply(messages)


def _openai_chat(messages: list[dict], *, json_mode: bool) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    kwargs: dict = {
        "model": settings.DEFAULT_OPENAI_MODEL,
        "messages": messages,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _anthropic_chat(messages: list[dict], *, json_mode: bool) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    system = ""
    converted: list[dict] = []
    for m in messages:
        if m["role"] == "system":
            system = (system + "\n" + m["content"]).strip()
        else:
            converted.append({"role": m["role"], "content": m["content"]})
    if json_mode:
        system = (system + "\n\n出力は必ず有効なJSONオブジェクトのみで返してください。").strip()
    resp = client.messages.create(
        model=settings.DEFAULT_ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system or "You are a helpful assistant.",
        messages=converted,
    )
    parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


# ----- Image understanding -----

DEFAULT_VISION_PROMPT = (
    "この画像に何が写っているか、内容・特徴・スタイル・読み取れる文字などを"
    "日本語で5〜10行程度で簡潔に説明してください。"
    "後で別のAIがこの説明文だけを読んで画像内容を把握できるよう、具体的に書いてください。"
)

VISION_MIME_FALLBACK = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def describe_image(file_path: str, prompt: str = DEFAULT_VISION_PROMPT) -> str:
    """Generate a Japanese description of an image using a vision-capable model.

    Returns an empty string if no key is configured or the call fails — callers
    can treat that as "no description available".
    """
    try:
        if not os.path.exists(file_path):
            return ""
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            ext = os.path.splitext(file_path)[1].lower()
            mime = VISION_MIME_FALLBACK.get(ext)
        if not mime or not mime.startswith("image/"):
            return ""
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("ascii")

        provider = settings.DEFAULT_PROVIDER
        if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return _anthropic_describe(b64, mime, prompt)
        if provider == "openai" and settings.OPENAI_API_KEY:
            return _openai_describe(b64, mime, prompt)
        if settings.OPENAI_API_KEY:
            return _openai_describe(b64, mime, prompt)
        if settings.ANTHROPIC_API_KEY:
            return _anthropic_describe(b64, mime, prompt)
        return ""
    except Exception:
        return ""


def _openai_describe(b64: str, mime: str, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.DEFAULT_OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def _anthropic_describe(b64: str, mime: str, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=settings.DEFAULT_ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": b64},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def build_rag_context(file_excerpts: Iterable[tuple[str, str]], max_chars: int = 6000) -> str:
    """Concatenate per-file excerpts into a context block for prompting."""
    out: list[str] = []
    used = 0
    for filename, text in file_excerpts:
        if not text:
            continue
        header = f"\n--- {filename} ---\n"
        block = header + text
        if used + len(block) > max_chars:
            block = block[: max_chars - used]
            out.append(block)
            break
        out.append(block)
        used += len(block)
    return "".join(out)


def assist_report(project_label: str, goal: str, file_summaries: list[dict]) -> dict:
    """Ask the model to produce a structured assist report.

    Returns a dict with classification / quality_score / feasibility / suggestions / summary.
    """

    instructions = (
        "あなたはノーコードAIプラットフォーム『Bloom』のアシスタントです。"
        "ユーザがアップロードしたデータを評価し、AIを作るためのアドバイスを返します。"
        "専門用語を避け、子供でも理解できる日本語で答えてください。"
    )
    user_prompt = (
        "以下はユーザのプロジェクト情報です。\n"
        f"- プロジェクト: {project_label}\n"
        f"- 目的: {goal or '(未記入)'}\n"
        f"- ファイル概要: {json.dumps(file_summaries, ensure_ascii=False)}\n\n"
        "次の JSON フォーマットだけを返してください（他の文章は禁止）:\n"
        "{\n"
        '  "classification": "短い分類ラベル",\n'
        '  "quality_score": 0から100の整数,\n'
        '  "feasibility": "low" | "medium" | "high",\n'
        '  "suggestions": ["具体的な改善提案", ...],\n'
        '  "summary": "ユーザ向けの2〜3文のまとめ"\n'
        "}"
    )

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt},
    ]
    raw = chat(messages, json_mode=True)
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {
            "classification": "未判定",
            "quality_score": 50,
            "feasibility": "medium",
            "suggestions": ["データを追加するとAIの精度が上がります。"],
            "summary": raw[:400] or "AIの応答を解析できませんでした。",
        }
    parsed.setdefault("classification", "未判定")
    parsed.setdefault("quality_score", 50)
    parsed.setdefault("feasibility", "medium")
    parsed.setdefault("suggestions", [])
    parsed.setdefault("summary", "")
    try:
        parsed["quality_score"] = max(0, min(100, int(parsed["quality_score"])))
    except Exception:
        parsed["quality_score"] = 50
    return parsed
