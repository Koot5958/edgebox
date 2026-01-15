from .parameters import MAX_LEN
from .lang_list import LANGUAGE_USES_SPACE


def join_text(text, lang):
    if text == []:
        return ""
    return " ".join(text) if LANGUAGE_USES_SPACE[lang] else "".join(text)


def split_text(text, lang):
    return text.split(" ") if LANGUAGE_USES_SPACE[lang] else text.split("")


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
            new_line = True
            prev_subt = new_prev_subt

    return new_line, prev_subt, subt