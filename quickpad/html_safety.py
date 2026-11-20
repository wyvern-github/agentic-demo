"""Conservative Qt HTML subset without executable or resource-bearing content."""

import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

from PyQt6.QtGui import QColor


_ALLOWED = {
    "p", "div", "br", "span", "b", "strong", "i", "em", "u", "s", "font",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "pre",
    "a",
}
_BLOCKED_CONTENT = {
    "head", "script", "style", "iframe", "object", "svg", "video", "audio",
    "form", "canvas", "template", "math", "noscript", "select", "textarea",
    "button", "frameset",
}
_VOID = {
    "area", "base", "br", "embed", "frame", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr",
}


def _safe_color(value: str) -> bool:
    if QColor(value).isValid():
        return True
    match = re.fullmatch(
        r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
        r"(?:\s*,\s*(0(?:\.\d+)?|1(?:\.0+)?|\d{1,3}%))?\s*\)",
        value,
        re.IGNORECASE,
    )
    return bool(match and all(int(part) <= 255 for part in match.group(1, 2, 3)))


def _safe_font_family(value: str) -> bool:
    component = r"""(?:'[^'\\;\r\n]*'|"[^"\\;\r\n]*"|[\w .+&\-]+)"""
    return bool(re.fullmatch(rf"\s*{component}(?:\s*,\s*{component})*\s*", value))


def _safe_style(style: str, preserve_whitespace: bool = False) -> str:
    allowed_values = {
        "font-style": {"normal", "italic", "oblique"},
        "text-align": {"left", "center", "right", "justify"},
        "vertical-align": {"baseline", "sub", "super"},
        "white-space": {"normal", "pre", "pre-wrap", "pre-line"},
        "list-style-type": {
            "none", "disc", "circle", "square", "decimal", "lower-alpha",
            "upper-alpha", "lower-roman", "upper-roman",
        },
    }
    clean: list[tuple[str, str]] = []
    for declaration in style.split(";"):
        if ":" not in declaration:
            continue
        name, value = (part.strip() for part in declaration.split(":", 1))
        name, lowered = name.lower(), value.lower()
        if not value or any(char in value for char in "\\<>{}@"):
            continue
        if name in allowed_values:
            valid = lowered in allowed_values[name]
        elif name == "font-weight":
            valid = bool(re.fullmatch(r"normal|bold|[1-9]00", lowered))
        elif name == "font-size":
            valid = bool(
                re.fullmatch(
                    r"(?:\d{1,3})(?:\.\d+)?(?:pt|px)|"
                    r"xx-small|x-small|small|medium|large|x-large|xx-large|smaller|larger",
                    lowered,
                )
            )
        elif name == "font-family":
            valid = _safe_font_family(value)
        elif name in {"-qt-list-indent", "-qt-block-indent"}:
            valid = bool(re.fullmatch(r"\d{1,2}", lowered))
        elif name == "text-decoration":
            words = lowered.split()
            valid = bool(words) and set(words) <= {"none", "underline", "line-through"}
        elif name in {"color", "background-color", "background"}:
            valid = _safe_color(value)
        else:
            valid = False
        if valid:
            clean.append((name, value))
    if preserve_whitespace and not any(name == "white-space" for name, _ in clean):
        clean.append(("white-space", "pre-wrap"))
    return "; ".join(f"{name}: {value}" for name, value in clean)


def _safe_href(value: str) -> bool:
    if not value or any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in value):
        return False
    if value.startswith("#"):
        return True
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    if parts.scheme.lower() in {"http", "https"}:
        return bool(parts.netloc)
    return parts.scheme.lower() == "mailto" and bool(parts.path)


class _Sanitizer(HTMLParser):
    def __init__(self, preserve_qt_whitespace: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.blocked: list[str] = []
        self.open_tags: list[str] = []
        self.preserve_qt_whitespace = preserve_qt_whitespace

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.blocked:
            if tag not in _VOID:
                self.blocked.append(tag)
            return
        if tag in _BLOCKED_CONTENT:
            self.blocked.append(tag)
            return
        output_tag = "div" if tag == "body" else tag
        if output_tag not in _ALLOWED:
            return
        if (
            self.preserve_qt_whitespace
            and output_tag in {"ul", "ol"}
            and self.open_tags
            and self.open_tags[-1] == "li"
            and self.output
            and self.output[-1].endswith("\n")
        ):
            self.output[-1] = self.output[-1][:-1]
        clean: list[tuple[str, str]] = []
        for name, value in attrs:
            if value is None:
                continue
            name = name.lower()
            value = value.strip()
            if name == "style":
                value = _safe_style(
                    value, self.preserve_qt_whitespace and output_tag in {"p", "li"}
                )
                if value:
                    clean.append((name, value))
            elif name == "align" and value.lower() in {"left", "center", "right", "justify"}:
                clean.append((name, value.lower()))
            elif output_tag == "a" and name == "href" and _safe_href(value):
                clean.append((name, value))
            elif output_tag == "font" and name in {"color", "bgcolor"} and _safe_color(value):
                clean.append((name, value))
            elif output_tag == "font" and name == "face" and _safe_font_family(value):
                clean.append((name, value))
            elif output_tag == "font" and name == "size" and re.fullmatch(r"[1-7]", value):
                clean.append((name, value))
        if (
            self.preserve_qt_whitespace
            and output_tag in {"p", "li"}
            and not any(name == "style" for name, _ in clean)
        ):
            clean.append(("style", "white-space: pre-wrap"))
        attributes = "".join(f' {name}="{escape(value, quote=True)}"' for name, value in clean)
        self.output.append(f"<{output_tag}{attributes}>")
        if output_tag not in _VOID:
            self.open_tags.append(output_tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.blocked:
            if tag in self.blocked:
                index = len(self.blocked) - 1 - self.blocked[::-1].index(tag)
                del self.blocked[index:]
            return
        output_tag = "div" if tag == "body" else tag
        if output_tag in _ALLOWED and output_tag not in _VOID:
            self.output.append(f"</{output_tag}>")
            if output_tag in self.open_tags:
                index = len(self.open_tags) - 1 - self.open_tags[::-1].index(output_tag)
                del self.open_tags[index:]

    def handle_data(self, data: str) -> None:
        if not self.blocked:
            self.output.append(escape(data))


def sanitize_html(source: str, *, preserve_qt_whitespace: bool = False) -> str:
    parser = _Sanitizer(preserve_qt_whitespace)
    parser.feed(source)
    parser.close()
    return "".join(parser.output)
