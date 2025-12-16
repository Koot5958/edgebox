from pathlib import Path
import re

from utils.parameters import MAX_LEN, REFRESH_RATE_SLOW
from utils.lang_list import LANGUAGE_USES_SPACE


TEMPLATE = (Path(__file__).parent / "subtitles_template.html").read_text(encoding="utf-8")


def join_text(text, lang):
    return " ".join(text) if LANGUAGE_USES_SPACE[lang] else "".join(text)


def split_text(text, lang):
    return text.split(" ") if LANGUAGE_USES_SPACE[lang] else text.split("")


def sanitize_html(html: str) -> str:
    # remove indentations
    html = re.sub(r'^[ \t]+', '', html, flags=re.MULTILINE)
    return html


def format_subt(text, prev_subt):
    new_line = False

    if len(text) <= MAX_LEN:
        subt = text
        prev_subt = []
    else:
        subt = text[(len(text) // MAX_LEN) * MAX_LEN :]
        start_subt = len(text) - len(subt)

        new_prev_subt = text[: start_subt]
        new_prev_subt = new_prev_subt[-MAX_LEN :]
        if prev_subt != new_prev_subt:
            prev_subt = new_prev_subt
            new_line = True

    return new_line, prev_subt, subt


def get_html_subt(prev_subt, subt, line_scroll, subt_type, subt_name, voice_level=0.0):
    html = TEMPLATE

    html = html.replace("{{SUBT_NAME}}", subt_name)
    html = html.replace("{{SUBT_TYPE}}", subt_type)
    html = html.replace("{{ANIM_DURATION}}", str(REFRESH_RATE_SLOW))
    html = html.replace("{{VOICE_LEVEL}}", f"{voice_level:.2f}")
    html = html.replace("{{ANIMATE_CLASS}}", "animate" if line_scroll else "")
    html = html.replace("{{PREV_SUBT}}", prev_subt if len(prev_subt) > 0 else "—")
    html = html.replace("{{SUBT}}", subt if len(subt) > 0 else "—")

    return sanitize_html(html)