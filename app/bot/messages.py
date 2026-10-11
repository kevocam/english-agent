from html import escape

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
    "/start — show this message"
)

NOT_OWNER = "🔒 This is a private bot."


def format_item(item: dict, index: int) -> str:
    lines = [
        f"<b>{index}. {escape(item['term'])}</b>  <i>{TYPE_LABEL.get(item['type'], item['type'])}</i>",
        escape(item["definition"]),
    ]
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
