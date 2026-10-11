"""Tutor conversacional con Claude: responde lo que escribas, corrige tu inglés
y explica usando tus items del día."""

from anthropic import AsyncAnthropic

from app import config

MAX_TURNS = 10  # mensajes recientes que se recuerdan (en memoria; se pierden al reiniciar)

SYSTEM = """You are Kevo's personal English tutor inside Telegram.

About Kevo: Peruvian, native Spanish speaker, Senior Full Stack Developer, English level B2.
He is taking a work English course about Agile/Scrum, mentoring and workplace communication.
Goal: speak and understand better, and actively USE his course vocabulary.

How to answer:
- If his message has English mistakes, start with one line: "✏️ Better: <corrected sentence>",
  then a very short why (max 1 line). Skip it if the message is correct.
- Then answer what he asked. Explain words simply, with 1–2 examples from software/Scrum work.
- When explaining a word, give a quick Spanish equivalent in parentheses, e.g. foster (fomentar).
- Answer in English. Switch to Spanish only if he writes in Spanish or seems lost.
- Keep it short: this is a phone chat. Max ~8 lines.
- End with a tiny challenge when it fits, e.g. "Try it: write a sentence with foster about your team."
- Plain text only (no Markdown, no ** or #). Emojis are fine.

Today's items (prioritize these in examples and challenges):
{items}"""


_client: AsyncAnthropic | None = None


def _anthropic() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _items_block(items: list[dict]) -> str:
    if not items:
        return "(none today)"
    return "\n".join(f"- {it['term']} ({it['type']}): {it['definition']}" for it in items)


async def reply(history: list[dict], text: str, items: list[dict]) -> str:
    """`history` se modifica in place: guarda el ida y vuelta para dar contexto."""
    history.append({"role": "user", "content": text})
    del history[:-MAX_TURNS]
    while history and history[0]["role"] != "user":  # la API exige empezar con user
        history.pop(0)

    try:
        response = await _anthropic().messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=600,
            system=SYSTEM.format(items=_items_block(items)),
            messages=list(history),
        )
    except Exception:
        history.pop()  # no dejar un mensaje sin respuesta en el historial
        raise
    answer = "".join(block.text for block in response.content if block.type == "text").strip()
    history.append({"role": "assistant", "content": answer})
    return answer
