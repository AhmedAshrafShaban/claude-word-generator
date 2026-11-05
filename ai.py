"""الربط مع Claude API: مخطط الفصول ثم كتابة كل فصل على حدة.
إذا لم يوجد ANTHROPIC_API_KEY يعمل التطبيق في الوضع التجريبي (demo) بنص جاهز،
بحيث يمكن تجربة بقية المسار (Word / PDF / الواجهة) دون أي تكلفة.
"""
import json
import os
import re

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-3-5")
NUM_CHAPTERS = 4
WORDS_PER_CHAPTER = int(os.environ.get("WORDS_PER_CHAPTER", "320"))
OUTLINE_MAX_TOKENS = 1200
CHAPTER_MAX_TOKENS = 2000

TONES = {
    "academic": "رسمية أكاديمية دقيقة، بجمل محكمة ومصطلحات واضحة",
    "simple": "مبسّطة وقريبة من القارئ العادي، بجمل قصيرة وأمثلة يسيرة",
    "literary": "أدبية رشيقة فيها حسّ جمالي دون تكلّف",
    "journalistic": "صحفية مباشرة، تبدأ بالمهم وتتجنب الحشو",
}

SYSTEM = (
    "أنت كاتب ومحرر عربي محترف. تكتب بعربية فصيحة سليمة خالية من الأخطاء النحوية "
    "والإملائية، دون تشكيل إلا عند الضرورة، ودون عبارات إنشائية فارغة. "
    "لا تذكر أنك نموذج ذكاء اصطناعي، ولا تضف مقدمات أو تعليقات خارج المطلوب."
)


def demo_mode():
    return not os.environ.get("ANTHROPIC_API_KEY")


def _client():
    from anthropic import Anthropic
    return Anthropic()


def _call(client, user, max_tokens, usage):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    usage["input_tokens"] += resp.usage.input_tokens
    usage["output_tokens"] += resp.usage.output_tokens
    return "".join(b.text for b in resp.content if b.type == "text")


def _json_from(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("لم يرجع النموذج JSON صالحاً")
    return json.loads(text[start : end + 1])


def _clean(s):
    return re.sub(r"[#*_`>]+", "", s).strip()


def parse_chapter(text):
    """يحوّل نص الفصل إلى كتل: ('h2', عنوان) أو ('p', فقرة)."""
    blocks, buf = [], []

    def flush():
        if buf:
            blocks.append(("p", _clean(" ".join(buf))))
            buf.clear()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            flush()
        elif line.startswith("###") or line.startswith("##"):
            flush()
            heading = _clean(line)
            if heading:
                blocks.append(("h2", heading))
        else:
            buf.append(line)
    flush()
    return [(k, v) for k, v in blocks if v]


def generate(idea, tone, progress):
    """يرجع (data, usage). data = {title, subtitle, chapters:[{title, blocks}]}"""
    usage = {"input_tokens": 0, "output_tokens": 0}
    if demo_mode():
        from demo import demo_document
        progress(20, "الوضع التجريبي: تجهيز نص جاهز")
        return demo_document(idea), usage

    client = _client()
    tone_desc = TONES.get(tone, TONES["academic"])

    progress(8, "تخطيط الفصول والعناوين")
    outline_prompt = (
        f"الفكرة: {idea}\n\n"
        f"ضع مخططاً لكتيّب قصير بنبرة {tone_desc}، من {NUM_CHAPTERS} فصول، "
        "آخرها خاتمة. لكل فصل عنوان واضح وعنوانان فرعيان.\n"
        'أجب بصيغة JSON فقط دون أي نص آخر وبهذا الشكل: '
        '{"title": "...", "subtitle": "...", "chapters": '
        '[{"title": "...", "sections": ["...", "..."]}]}'
    )
    outline = None
    for _ in range(2): 
        try:
            outline = _json_from(_call(client, outline_prompt, OUTLINE_MAX_TOKENS, usage))
            break
        except (ValueError, json.JSONDecodeError):
            continue
    if not outline or not outline.get("chapters"):
        raise RuntimeError("تعذّر الحصول على مخطط صالح من النموذج، أعد المحاولة.")

    chapters = outline["chapters"][:NUM_CHAPTERS]
    result = {
        "title": _clean(outline.get("title", idea))[:120],
        "subtitle": _clean(outline.get("subtitle", "")),
        "chapters": [],
    }
    outline_text = "\n".join(
        f"{i}. {c['title']}" for i, c in enumerate(chapters, 1)
    )
    for i, ch in enumerate(chapters, 1):
        progress(15 + int(60 * (i - 1) / len(chapters)), f"كتابة الفصل {i} من {len(chapters)}")
        sections = "\n".join(f"- {s}" for s in ch.get("sections", []))
        prompt = (
            f"عنوان الكتيّب: {result['title']}\nالفكرة: {idea}\nفصول الكتيّب:\n{outline_text}\n\n"
            f"اكتب نص الفصل {i}: «{ch['title']}» بنبرة {tone_desc}، في نحو {WORDS_PER_CHAPTER} كلمة.\n"
            "الشكل المطلوب: فقرة تمهيدية قصيرة بلا عنوان، ثم لكل عنوان فرعي من التالية سطر يبدأ بـ ### "
            f"ثم فقرة أو فقرتان:\n{sections}\n"
            "نص عادي فقط: بلا قوائم نقطية ولا ترقيم ولا خط عريض، وافصل الفقرات بسطر فارغ."
        )
        blocks = parse_chapter(_call(client, prompt, CHAPTER_MAX_TOKENS, usage))
        if not blocks:
            raise RuntimeError(f"رجع الفصل {i} فارغاً، أعد المحاولة.")
        result["chapters"].append({"title": _clean(ch["title"]), "blocks": blocks})
    progress(75, "اكتملت كتابة المحتوى")
    return result, usage


if __name__ == "__main__":
    def my_progress(percent, msg):
        print(f"[{percent}%] {msg}")

    idea = "أهمية القراءة السريعة"
    
    print("جاري بدء التشغيل...")
    result, usage = generate(idea, "simple", my_progress)
    
    print("\n--- النتيجة النهائية ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))