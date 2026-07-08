import unicodedata
import re


def normalize(text):
    """回答判定用に文字列を正規化する"""

    if text is None:
        return ""

    # 前後の空白を削除
    text = text.strip()

    # 全角英数字 → 半角、半角カナ → 全角などを統一
    text = unicodedata.normalize("NFKC", text)

    # 大文字小文字を統一
    text = text.lower()

    # 記号・空白を除去
    text = re.sub(r"[\s\-_/・]", "", text)

    return text


def make_hint(word, hint_count):
    """
    hint_count文字だけ表示し、残りは「_」にする
    """
    return word[:hint_count] + "_" * (len(word) - hint_count)


def is_correct_answer(question, answer):
    answer = normalize(answer)

    if answer == normalize(question.word):
        return True

    return any(answer == normalize(alias.alias) for alias in question.aliases.all())
