import html
import re

# https://github.com/HFrost0/bilix/blob/41fa4b3ca59ee724a943585ba09c93ff4ca28e9f/bilix/utils.py
def legal_title(*parts: str, join_str: str = '-'):
    """
    join several string parts to os illegal file/dir name (no illegal character and not too long).
    auto skip empty.

    :param parts:
    :param join_str: the string to join each part
    :return:
    """
    return join_str.join(filter(lambda x: len(x) > 0, map(replace_illegal, parts)))


def replace_illegal(s: str):
    """strip, unescape html and replace os illegal character in s"""
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n\t]", '', s)  # replace illegal filename character
    return s