"""Unicode-aware word counting and literal search over normalized document text."""

import unicodedata


def word_count(text: str) -> int:
    count = 0
    has_letter_or_number = False
    for character in text:
        category = unicodedata.category(character)[0]
        if category in {"L", "N"}:
            has_letter_or_number = True
        elif category != "M":
            count += int(has_letter_or_number)
            has_letter_or_number = False
    return count + int(has_letter_or_number)


def codepoint_to_qt(text: str, offset: int) -> int:
    if not 0 <= offset <= len(text):
        raise ValueError("Code-point offset is outside the document.")
    return len(text[:offset].encode("utf-16-le", errors="surrogatepass")) // 2


def qt_to_codepoint(text: str, position: int) -> int:
    if position < 0:
        raise ValueError("Qt position is outside the document.")
    units = 0
    for index, character in enumerate(text):
        if units == position:
            return index
        units += 2 if ord(character) > 0xFFFF else 1
        if units > position:
            raise ValueError("Qt position splits a surrogate pair.")
    if units == position:
        return len(text)
    raise ValueError("Qt position is outside the document.")


def find_matches(
    text: str, query: str, *, match_case: bool = False, overlapping: bool = False
) -> list[tuple[int, int]]:
    if not query:
        return []
    if match_case:
        matches = []
        start = 0
        while (position := text.find(query, start)) != -1:
            end = position + len(query)
            matches.append((position, end))
            start = position + 1 if overlapping else end
        return matches

    folded_parts: list[str] = []
    original_indices: list[int] = []
    for index, character in enumerate(text):
        folded = character.casefold()
        folded_parts.append(folded)
        original_indices.extend([index] * len(folded))
    folded_text = "".join(folded_parts)
    folded_query = query.casefold()
    if not folded_query:
        return []
    matches = []
    start = 0
    while (position := folded_text.find(folded_query, start)) != -1:
        end = position + len(folded_query)
        start_boundary = position == 0 or original_indices[position - 1] != original_indices[position]
        end_boundary = end == len(original_indices) or original_indices[end - 1] != original_indices[end]
        if start_boundary and end_boundary:
            matches.append((original_indices[position], original_indices[end - 1] + 1))
            start = position + 1 if overlapping else end
        else:
            start = position + 1
    return matches
