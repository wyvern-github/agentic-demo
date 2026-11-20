"""Real file round trips, formatting loss, atomicity, and HTML safety."""

import pytest

from PyQt6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import (
    QColor, QDragEnterEvent, QDropEvent, QFont, QImage, QTextCursor, QTextDocument,
    QTextFormat, QTextListFormat,
)
from PyQt6.QtWidgets import QApplication, QColorDialog, QFileDialog, QMessageBox

from quickpad import storage
from quickpad.document import SafeTextDocument, has_rich_content
from quickpad.html_safety import sanitize_html


def choose_save(monkeypatch, path, selected_filter="Text files (*.txt)"):
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), selected_filter)
    )


def choose_open(monkeypatch, path):
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))


def select(editor, start, end):
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


def char_format(editor, index):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(index + 1)
    return cursor.charFormat()


def record_errors(monkeypatch):
    errors = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: errors.append(args[1:]) or QMessageBox.StandardButton.Ok
    )
    return errors


def test_text_save_as_adds_extension_and_reopens_utf8(window, monkeypatch, tmp_path):
    target = tmp_path / "notes"
    choose_save(monkeypatch, target)
    window.editor.insertPlainText("First line\ncaf\u00e9")
    assert window.save_as()
    saved = tmp_path / "notes.txt"
    assert saved.read_bytes() == "First line\ncaf\u00e9".encode("utf-8")
    assert window.current_path == saved
    assert not window.editor.document().isModified()

    window.editor.insertPlainText(" changed")
    choose_open(monkeypatch, saved)
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Discard
    )
    assert window.open_document()
    assert window.editor.toPlainText() == "First line\ncaf\u00e9"
    assert window.current_path == saved
    assert not window.editor.document().isModified()


def test_menu_actions_save_and_open_html_with_selected_extension(window, monkeypatch, tmp_path):
    target = tmp_path / "report"
    choose_save(monkeypatch, target, "HTML files (*.html)")
    window.editor.insertPlainText("from actions")
    window.save_action.trigger()
    saved = tmp_path / "report.html"
    assert saved.exists()
    assert window.current_path == saved
    assert window.new_document()
    choose_open(monkeypatch, saved)
    window.open_action.trigger()
    assert window.editor.toPlainText() == "from actions"
    assert window.current_path == saved


def test_bom_is_preserved_and_undo_returns_to_saved_baseline(window, monkeypatch, tmp_path):
    target = tmp_path / "bom.txt"
    target.write_bytes(storage.UTF8_BOM + "caf\u00e9".encode("utf-8"))
    choose_open(monkeypatch, target)
    assert window.open_document()
    assert window.editor.toPlainText() == "caf\u00e9"
    window.editor.moveCursor(QTextCursor.MoveOperation.End)
    window.editor.insertPlainText("!")
    assert window.save_document()
    assert target.read_bytes() == storage.UTF8_BOM + "caf\u00e9!".encode("utf-8")
    window.undo_action.trigger()
    assert window.editor.document().isModified()
    window.redo_action.trigger()
    assert not window.editor.document().isModified()


def test_html_round_trip_retains_formatting_lists_and_spaces(window, monkeypatch, tmp_path):
    text = "Bold   italic\nColor list"
    window.editor.setPlainText(text)
    select(window.editor, 0, 4)
    window.formatting.bold_action.trigger()
    select(window.editor, 7, 13)
    window.formatting.italic_action.trigger()
    select(window.editor, 14, 19)
    window.formatting.underline_action.trigger()
    window.formatting.font_family.setEditText("QuickPad Test Sans")
    window.formatting.font_size.setValue(18)
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#aa1122"))
    window.formatting.color_action.trigger()
    select(window.editor, 1, 1)
    window.formatting.align_actions[Qt.AlignmentFlag.AlignRight].trigger()
    select(window.editor, 16, 16)
    window.formatting.bullet_action.trigger()

    target = tmp_path / "formatted.html"
    choose_save(monkeypatch, target, "HTML files (*.html)")
    assert window.save_as()
    saved_html = target.read_text(encoding="utf-8")
    assert "font-weight: 700" in saved_html
    assert "font-style: italic" in saved_html
    assert "color: #aa1122" in saved_html
    assert "<style" not in saved_html.lower()

    assert window.new_document()
    choose_open(monkeypatch, target)
    assert window.open_document()
    assert window.editor.toPlainText() == text
    assert char_format(window.editor, 1).fontWeight() == QFont.Weight.Bold
    assert char_format(window.editor, 8).fontItalic()
    color_format = char_format(window.editor, 15)
    assert color_format.fontUnderline()
    assert color_format.fontFamilies() == ["QuickPad Test Sans"]
    assert color_format.fontPointSize() == 18
    assert color_format.foreground().color() == QColor("#aa1122")
    first = window.editor.document().begin()
    assert first.blockFormat().alignment() & Qt.AlignmentFlag.AlignRight
    assert first.next().textList().format().style() == QTextListFormat.Style.ListDisc
    assert not window.editor.document().isModified()


@pytest.mark.parametrize(
    "alignment",
    [
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignHCenter,
        Qt.AlignmentFlag.AlignRight,
        Qt.AlignmentFlag.AlignJustify,
    ],
)
def test_html_round_trip_preserves_each_alignment(window, monkeypatch, tmp_path, alignment):
    window.editor.insertPlainText("paragraph")
    window.formatting.align_actions[alignment].trigger()
    target = tmp_path / "aligned.html"
    choose_save(monkeypatch, target, "HTML files (*.html)")
    assert window.save_as()
    assert window.new_document()
    choose_open(monkeypatch, target)
    assert window.open_document()
    assert window.editor.document().begin().blockFormat().alignment() & alignment


def test_html_round_trip_preserves_headings_fonts_background_and_nested_lists(
    window, monkeypatch, tmp_path
):
    source = tmp_path / "source.html"
    source.write_text(
        """<h1>Heading</h1>
        <p><span style="font-family:'Font+ (UI)'; background-color:#ffff00;
        text-decoration:line-through">styled</span></p>
        <ul><li>outer<ul><li>inner</li></ul></li></ul>""",
        encoding="utf-8",
    )
    choose_open(monkeypatch, source)
    assert window.open_document()
    before_text = window.editor.toPlainText()
    first = window.editor.document().begin()
    before_heading_size = first.begin().fragment().charFormat().intProperty(
        QTextFormat.Property.FontSizeAdjustment
    )

    target = tmp_path / "roundtrip.html"
    choose_save(monkeypatch, target, "HTML files (*.html)")
    assert window.save_as()
    assert window.new_document()
    choose_open(monkeypatch, target)
    assert window.open_document()
    assert window.editor.toPlainText() == before_text
    heading = window.editor.document().begin()
    assert heading.blockFormat().headingLevel() == 1
    assert heading.begin().fragment().charFormat().intProperty(
        QTextFormat.Property.FontSizeAdjustment
    ) == before_heading_size
    styled = heading.next().begin().fragment().charFormat()
    assert styled.fontFamilies() == ["Font+ (UI)"]
    assert styled.fontStrikeOut()
    assert styled.background().color() == QColor("#ffff00")
    outer = heading.next().next()
    inner = outer.next()
    assert outer.textList().format().indent() == 1
    assert inner.textList().format().indent() == 2


def test_unsafe_html_is_removed_and_no_resource_is_fetched(
    window, monkeypatch, tmp_path, qtbot
):
    source = tmp_path / "untrusted.html"
    source.write_text(
        """<html><head><style>body{background:url(file:///secret)}</style>
        <link rel="stylesheet" href="https://example.invalid/style.css"></head>
        <body onload="bad()"><p>before<img src="file:///secret.png">
        <script>remove-script</script><form><b>remove-form</b></form>
        <svg><text>remove-svg</text></svg><object>remove-object</object>
        <span onclick="bad()" style="font-weight:700; font-style:italic;
        color:#ff0000; background-image:url(https://example.invalid/img)">safe</span>
        <a href="javascript:bad()">bad link</a>
        <a href="https://example.invalid/path">safe link</a></p></body></html>""",
        encoding="utf-8",
    )
    calls = []
    original = SafeTextDocument.loadResource

    def tracked(document, kind, url):
        calls.append(url.toString())
        return original(document, kind, url)

    monkeypatch.setattr(SafeTextDocument, "loadResource", tracked)
    choose_open(monkeypatch, source)
    assert window.open_document()
    qtbot.wait(30)
    text = window.editor.toPlainText()
    assert "before" in text and "safe" in text
    assert all(word not in text for word in ("remove-script", "remove-form", "remove-svg", "remove-object"))
    safe_index = text.index("safe")
    assert char_format(window.editor, safe_index).fontWeight() == QFont.Weight.Bold
    assert char_format(window.editor, safe_index).fontItalic()
    assert char_format(window.editor, safe_index).foreground().color() == QColor("#ff0000")
    assert calls == []

    destination = tmp_path / "safe.html"
    choose_save(monkeypatch, destination, "HTML files (*.html)")
    assert window.save_as()
    html = destination.read_text(encoding="utf-8").lower()
    assert all(
        forbidden not in html
        for forbidden in ("<img", "<script", "<style", "<form", "<svg", "<object", "javascript:", "url(", "file:")
    )
    assert 'href="https://example.invalid/path"' in html
    assert calls == []
    resource = window.editor.document().resource(
        QTextDocument.ResourceType.ImageResource, QUrl.fromLocalFile(str(tmp_path / "secret.png"))
    )
    assert resource is None
    assert len(calls) == 1


def test_sanitizer_rejects_obfuscated_schemes_and_resource_css():
    html = sanitize_html(
        '<p><a href="java&#x73;cript:alert(1)">bad</a>'
        '<a href="file:///private">file</a>'
        '<span style="color:#ff0000; background: u\\72l(file:///x);'
        'font-weight:700; background-image:url(https://example.invalid)">safe</span></p>'
    ).lower()
    assert "javascript:" not in html
    assert "file:" not in html
    assert "url(" not in html
    assert "background" not in html
    assert "font-weight: 700" in html
    assert "color: #ff0000" in html


def test_image_drag_is_rejected_and_html_drop_becomes_plain_text(window):
    viewport = window.editor.viewport()
    image = QMimeData()
    image.setImageData(QImage(2, 2, QImage.Format.Format_RGB32))
    drag = QDragEnterEvent(
        QPoint(5, 5), Qt.DropAction.CopyAction, image,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, drag)
    assert not drag.isAccepted()
    image_drop = QDropEvent(
        QPointF(5, 5), Qt.DropAction.CopyAction, image,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, image_drop)
    assert not image_drop.isAccepted()
    assert window.editor.toPlainText() == ""
    assert "<img" not in window.editor.toHtml().lower()

    mixed = QMimeData()
    mixed.setText("dropped text")
    mixed.setHtml('<img src="https://example.invalid/x.png"><b>dropped text</b>')
    drag = QDragEnterEvent(
        QPoint(5, 5), Qt.DropAction.CopyAction, mixed,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, drag)
    assert drag.isAccepted()
    drop = QDropEvent(
        QPointF(5, 5), Qt.DropAction.CopyAction, mixed,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, drop)
    assert window.editor.toPlainText() == "dropped text"
    assert "<img" not in window.editor.toHtml().lower()


@pytest.mark.parametrize(
    "kind", ["bold", "italic", "underline", "family", "size", "color", "alignment", "bullets"]
)
def test_supported_formatting_always_warns_before_plain_save(
    window, monkeypatch, tmp_path, kind
):
    window.editor.setPlainText("formatted")
    select(window.editor, 0, len("formatted"))
    controls = window.formatting
    if kind in {"bold", "italic", "underline"}:
        getattr(controls, f"{kind}_action").trigger()
    elif kind == "family":
        controls.font_family.setEditText("QuickPad Test Sans")
    elif kind == "size":
        controls.font_size.setValue(23)
    elif kind == "color":
        monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#aa1122"))
        controls.color_action.trigger()
    elif kind == "alignment":
        controls.align_actions[Qt.AlignmentFlag.AlignHCenter].trigger()
    else:
        controls.bullet_action.trigger()
    assert has_rich_content(window.editor)
    before_html = window.editor.toHtml()
    before_modified = window.editor.document().isModified()
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args[1]) or QMessageBox.StandardButton.Cancel,
    )
    target = tmp_path / "loss.txt"
    choose_save(monkeypatch, target)
    assert not window.save_as()
    assert warnings == ["Formatting will be lost"]
    assert not target.exists()
    assert window.editor.toHtml() == before_html
    assert window.editor.document().isModified() == before_modified
    assert window.current_path is None


def test_confirmed_plain_conversion_establishes_plain_clean_baseline(
    window, monkeypatch, tmp_path
):
    html_path = tmp_path / "original.html"
    window.editor.insertPlainText("Important text")
    choose_save(monkeypatch, html_path, "HTML files (*.html)")
    assert window.save_as()
    select(window.editor, 0, len("Important text"))
    window.formatting.bold_action.trigger()
    target = tmp_path / "plain.txt"
    target.write_bytes(b"old")
    choose_save(monkeypatch, target)
    before_html = window.editor.toHtml()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Cancel)
    assert not window.save_as()
    assert target.read_bytes() == b"old"
    assert window.current_path == html_path
    assert window.editor.toHtml() == before_html
    assert window.editor.document().isModified()

    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes)
    assert window.save_as()
    assert target.read_bytes() == b"Important text"
    assert window.current_path == target
    assert window.editor.toPlainText() == "Important text"
    assert not has_rich_content(window.editor)
    assert not window.editor.document().isModified()
    assert not window.undo_action.isEnabled()


def test_explicit_default_color_still_warns_and_flattens(window, monkeypatch, tmp_path):
    window.editor.insertPlainText("plain-looking")
    select(window.editor, 0, len("plain-looking"))
    default_color = window.editor.palette().text().color()
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: default_color)
    window.formatting.color_action.trigger()
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args[1]) or QMessageBox.StandardButton.Yes,
    )
    target = tmp_path / "plain.txt"
    choose_save(monkeypatch, target)
    assert window.save_as()
    assert warnings == ["Formatting will be lost"]
    assert not has_rich_content(window.editor)
    assert not window.editor.document().isModified()


def test_failed_atomic_commit_preserves_old_file_and_rich_editor(
    window, monkeypatch, tmp_path
):
    original = tmp_path / "original.html"
    window.editor.insertPlainText("Keep this")
    choose_save(monkeypatch, original, "HTML files (*.html)")
    assert window.save_as()
    select(window.editor, 0, len("Keep this"))
    window.formatting.bold_action.trigger()
    target = tmp_path / "existing.txt"
    target.write_bytes(b"old bytes")
    before = window.editor.toHtml()
    choose_save(monkeypatch, target)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes)
    errors = record_errors(monkeypatch)
    real_save_file = storage.QSaveFile

    class CancelledCommit(real_save_file):
        def commit(self):
            self.cancelWriting()
            return super().commit()

    monkeypatch.setattr(storage, "QSaveFile", CancelledCommit)
    assert not window.save_as()
    assert errors and errors[0][0] == "Save failed"
    assert target.read_bytes() == b"old bytes"
    assert window.current_path == original
    assert window.editor.toHtml() == before
    assert window.editor.document().isModified()


def test_real_save_error_and_unsupported_extension_preserve_state(window, monkeypatch, tmp_path):
    window.editor.insertPlainText("unsaved")
    directory = tmp_path / "directory.txt"
    directory.mkdir()
    errors = record_errors(monkeypatch)
    choose_save(monkeypatch, directory)
    assert not window.save_as()
    assert directory.is_dir()
    choose_save(monkeypatch, tmp_path / "unsupported.rtf")
    assert not window.save_as()
    assert len(errors) == 2
    assert window.current_path is None
    assert window.editor.toPlainText() == "unsaved"
    assert window.editor.document().isModified()


def test_save_as_cancel_preserves_path_format_and_dirty_state(window, monkeypatch, tmp_path):
    original = tmp_path / "original.html"
    window.editor.insertPlainText("original")
    choose_save(monkeypatch, original, "HTML files (*.html)")
    assert window.save_as()
    select(window.editor, 0, len("original"))
    window.formatting.bold_action.trigger()
    before = window.editor.toHtml()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    assert not window.save_as()
    assert window.current_path == original
    assert window.editor.toHtml() == before
    assert window.editor.document().isModified()


def test_saving_without_a_filename_reports_an_error(window, monkeypatch, tmp_path):
    window.editor.insertPlainText("keep")
    choose_save(monkeypatch, tmp_path.anchor)
    errors = record_errors(monkeypatch)
    assert not window.save_as()
    assert errors and errors[0][0] == "Save failed"
    assert window.current_path is None
    assert window.editor.toPlainText() == "keep"
    assert window.editor.document().isModified()
