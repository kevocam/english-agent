from html import escape
from urllib.parse import quote

from telegram import LinkPreviewOptions

# Sin preview: con 3 links de audio el mensaje se llenaría de tarjetas
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)

TYPE_LABEL = {
    "vocab": "📘 Vocab",
    "phrasal": "🔗 Phrasal verb",
    "idiom": "💬 Expression",
    "grammar": "🧩 Grammar",
}

WELCOME = (
    "👋 <b>Hi Kevo!</b> I'm your English agent.\n\n"
    "Every day I'll send you a few words and structures from your B2 course, "
    "and I'll keep reminding you until you practice them.\n\n"
    "Commands:\n"
    "/hoy — today's items\n"
    "/start — show this message\n\n"
    "💬 Or just write to me in English: ask about a word, or practice a sentence and I'll correct it."
)

NOT_OWNER = "🔒 This is a private bot."
NO_LLM = "⚙️ The tutor isn't configured yet (missing ANTHROPIC_API_KEY)."
TUTOR_ERROR = "😵 Oops, I couldn't answer that right now. Try again in a minute."


def listen_url(item: dict) -> str:
    """YouGlish: clips reales de YouTube con la palabra dicha por nativos (inglés US)."""
    spoken = item.get("spoken") or item["term"]
    return f"https://youglish.com/pronounce/{quote(spoken)}/english/us"


def format_item(item: dict, index: int) -> str:
    lines = [
        f"<b>{index}. {escape(item['term'])}</b>  <i>{TYPE_LABEL.get(item['type'], item['type'])}</i>",
    ]
    pron = f"🗣 <code>{escape(item['ipa'])}</code>  " if item.get("ipa") else "🗣 "
    lines.append(f'{pron}<a href="{escape(listen_url(item))}">🔊 listen</a>')
    lines.append(escape(item["definition"]))
    if item.get("example"):
        lines.append(f"✏️ <i>{escape(item['example'])}</i>")
    return "\n".join(lines)


def format_today(items: list[dict]) -> str:
    if not items:
        return "🎉 Nothing due today. You've seen everything for now!"
    body = "\n\n".join(format_item(it, i) for i, it in enumerate(items, start=1))
    return f"☀️ <b>Today's items</b>\n\n{body}"


MOTIVATION = [
    "Small steps every day beat one big push. Let's go! 💪",
    "Today's goal: use at least one of these words in a real conversation.",
    "Your future self in that English interview says thanks. 🙌",
    "Read them out loud once. Your speaking will thank you.",
    "Consistency > intensity. Three words, every day.",
    "Try to sneak one of these into a Slack message today. 😉",
    "Good morning! New day, new words.",
]


def format_morning(items: list[dict], day_index: int) -> str:
    motivation = MOTIVATION[day_index % len(MOTIVATION)]
    return f"🌅 <b>Good morning, Kevo!</b>\n<i>{escape(motivation)}</i>\n\n" + format_today(items)


NUDGES = [
    "⏰ <b>Quick reminder</b> — your exercise is waiting:",
    "👀 <b>Still there, Kevo?</b> Just one answer:",
    "🔔 <b>Kevo!</b> 2 minutes of English, let's go:",
]


def format_nudge(exercise: str, nudge_count: int) -> str:
    head = NUDGES[min(nudge_count, len(NUDGES) - 1)]
    return f"{head}\n{escape(exercise)}"
