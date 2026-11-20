# Findings

### P1 — Saving HTML corrupts empty paragraphs

**Location:** `quickpad\html_safety.py:84`, `quickpad\main_window.py:223`

In an actual offscreen save-on-close flow, a document containing
`First\n\nSecond` was saved as HTML after choosing Save. Reopening it produced
`First\n\n\nSecond`; the reopened document was clean. Qt's original HTML
round-trips correctly, but the sanitizer removes its
`-qt-paragraph-type:empty` marker. Restoring that marker in the sanitized HTML
restored the original text. Empty, leading, and trailing paragraphs are also
affected. The close guard therefore permits closing after saving a different
document from the one visible to the user.

Preserve empty-paragraph semantics in the safe Qt HTML subset. Add file
round-trip and save-on-close tests for empty documents and leading, trailing,
and consecutive blank paragraphs, including dirty-state assertions.

### P1 — Saving a plain file silently changes non-breaking spaces

**Location:** `quickpad\main_window.py:218`

An actual UTF-8 file containing `b'Price\xc2\xa0100'` was opened and saved
without editing. The document's raw text still contained U+00A0, but
`toPlainText()` returned an ordinary space; Save overwrote the file with
`b'Price 100'`, without a warning, and marked the document clean. Thus even a
no-op Save can destroy meaningful Unicode text and leave the clean editor
different from what will reopen.

Preserve literal text characters when extracting text for saving, while
handling Qt's structural paragraph separators deliberately. Add byte-exact
UTF-8/BOM round trips for U+00A0, both unchanged and after edits.

### P2 — Literal search and replace conflate non-breaking and ordinary spaces

**Location:** `quickpad\search.py:27`, `quickpad\search.py:69`,
`quickpad\search.py:145`

For raw document text `A\u00a0B C`, Replace All of an ordinary space with `_`
reported two matches and produced `A_B_C`; only the last space was literal.
Searching for U+00A0 through `DocumentSearch` returned no match, and the find
input itself converted a U+00A0 query to an ordinary space. Undo did restore
the original raw text in the probe. This can replace characters the user did
not search for.

Use character-preserving document and query extraction, with consistent
code-point/Qt-position conversion. Add literal-space versus U+00A0 search and
replacement tests, including emoji, paragraph boundaries, and undo.

### P2 — Supported HTML list styles are lost on open or save

**Location:** `quickpad\html_safety.py:135`

Opening `<ol style="list-style-type: lower-alpha"><li>one</li><li>two</li></ol>`
produced a lower-alpha list. After an actual HTML save and reopen, it was a
decimal list: Qt serialized the style as `type="a"`, which the sanitizer
discarded. A source `<ol type="a">` already became decimal on opening;
square bullets likewise became discs on a save/reopen. The user loses list
formatting without any loss warning.

Allow only validated Qt-supported `type` values on list elements, while still
rejecting unsafe attributes. Test both direct import and saved round trips for
alphabetic, Roman, circle, and square styles.

### P2 — The HTML sanitizer drops accepted font-family names

**Location:** `quickpad\html_safety.py:61`

Selecting text, entering `@MS Gothic` in the font-family control, saving as
HTML, and reopening changed the character-format family from
`['@MS Gothic']` to `['Sans Serif']`. Qt's unsanitized HTML preserved the
family, but the sanitizer discarded the declaration because it contains
`@`. The offscreen font database was empty, so this verifies loss of font
metadata, not on-screen glyph rendering. A clean save can silently lose a
selected family.

Parse and validate quoted font-family values without rejecting safe `@`
characters; do not loosen the resource/CSS safety checks. Add font-family
round-trip tests alongside malicious-style tests.

### P2 — Paragraph formatting reaches beyond the selected range

**Location:** `quickpad\formatting.py:80`, `quickpad\formatting.py:150`

With `first\nsecond\nthird`, select `first\nsecond\n`, ending exactly at the
start of `third`. Applying bullets or right alignment also formats the
unselected third paragraph. Toggling bullets off again removes them from the
first two paragraphs but leaves the unintended bullet on the third. The
application changes and may save formatting outside the selection.

Treat a selection end at the next block's start as exclusive for both
alignment and bullet creation, consistent with bullet removal. Test forward
and backward selections ending at block boundaries, plus undo.

### P2 — Replace All blocks the UI for a modest document

**Location:** `quickpad\search.py:75`, `quickpad\text_service.py:22`

Replacing spaces in `'word ' * 20000` (100,000 characters, 20,000 matches)
took 8.46 seconds in this environment. A Qt timer scheduled for 100 ms fired
only after 8.47 seconds, confirming that the UI event loop was blocked.
Each match converts two offsets by slicing and UTF-16-encoding a document
prefix, contributing quadratic work; individual document edits may add cost.

Precompute offset conversions and batch or otherwise bound replacement work
while retaining formatting and the single undo operation. Add a
responsiveness/scaling regression check and verify undo and Unicode offsets.

No P0 or P3 findings were identified.

## Verdict and scope

**CHANGES REQUIRED** — two P1 and five P2 findings remain open.

- **Date:** 2026-11-20.
- **Branch:** `experiment/no-helpers`.
- **Review HEAD:** `18484f63f9b4ddcc5429bcc07743918b77bec866`.
- **Requested baseline:** `60a3f9d3c18f23976b83e5b6ba95359dff09a65e`,
  verified as an existing commit. No baseline fallback was needed. It is not
  an ancestor of HEAD because of the recorded identity rewrite. Its tree is
  `e583ad462e207ad914231b5ac06f2ad3392c122d`, identical to rewritten initial
  commit `76bf88ff4a7fcced45731792b7f00038608a06d8`. The cumulative tree diff
  uses the exact requested baseline; the rewritten root explains the four
  milestone commits' history.
- **State:** no staged changes or untracked product paths were present before
  this report. Tracked application, tests, manifest, and README matched HEAD.
  The only tracked local modification was the pre-existing `HANDOFF.md`
  post-commit receipt; this report is a new untracked file. HEAD is therefore
  not an exact snapshot of the whole reviewed worktree. Pre-existing ignored
  environments, caches, and egg metadata were not treated as product changes.
- **Examined:** the complete application and entry point, all tests and
  fixtures, dependency manifest, README, planning artifacts, cumulative
  baseline diff, commit history, staged/unstaged state, and the local handoff
  receipt. There was no prior `REVIEW.md`. Both applicable Python/pytest
  instruction files were checked and were absent.

## Acceptance coverage

| Criteria | Evidence and limitations |
|---|---|
| 1 | Offscreen startup, focus, shortcuts, and 600×400 geometry were exercised. Native appearance and high-DPI behavior were not checked. |
| 2, 10, 11 | The suite exercised Save/Discard/Cancel, same-target Open, cancellation, real I/O errors, and a cancelled atomic commit. The successful-save corruption in the first two findings still undermines document safety. |
| 3 | Tests cover explicit formatting-loss confirmation, cancel/failure preservation, and plain conversion. U+00A0 is nevertheless silently changed on an ordinary text save. |
| 4 | The suite checks representative unsafe HTML and blocked resource loading; this was not an exhaustive security proof. |
| 5, 6 | Typical character formatting, alignment, bullets, and undo pass; boundary selections and the stated HTML font/list round trips fail. |
| 7, 8 | Literal, overlap, casefold, emoji, combining-text, and undo tests pass for their covered inputs; U+00A0 matching/replacement and Replace All responsiveness fail. |
| 9 | Unicode word-count and live-update tests pass for their covered inputs. |
| 12 | Source, filters, and tests support the stated no-image/no-RTF/no-database boundaries. |

## Checks and evidence

The full current suite was run independently with Python 3.12.10, PyQt
6.12.1, and Qt runtime 6.12.0:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_ADDOPTS = ''
& .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .review-verify-c2565a9a-20261120
```

Result: **89 passed in 1.25s**. The unique session-owned test directory and
reproduction files were removed after use; pre-existing files were not
removed. This reproduces the M4/final suite count in `MILESTONES.md`; the
earlier milestone counts were not rerun at their historical commits. Passing
tests do not cover the findings above.

Additional offscreen Python/QTest probes were run via
`& .\.venv\Scripts\python.exe -` with inline scripts:

- Actual file open/save/reopen and Save-on-Close used `QSaveFile` with
  monkeypatched file/message dialogs; the observed contents and list/font
  metadata are recorded in the findings.
- A separate reference compared **21,756** casefold/overlap cases, using
  short strings containing ASCII case pairs, `ß`, emoji, and a combining
  mark; all comparisons passed. This did not include U+00A0.
- Keyboard events exercised Ctrl+A/B/I/U/Z, Ctrl+L/E/R/J, Ctrl+F/H and F3,
  Ctrl+S/O/N and Ctrl+Shift+S with cancellation, and Alt+F then X invoking
  the close guard. Shift+Tab reached both font controls at 600×400.
  `StandardKey.Quit` had no direct binding in this Qt environment; native
  window-manager close shortcuts were not tested.
- `runpy.run_module('quickpad', run_name='__main__')` inside an existing
  offscreen `QApplication`, with a `QTimer`, verified a responsive event
  loop and a visible, clean 960×640 editor. The developer's separate
  five-second `python -m quickpad` launch is recorded in `HANDOFF.md`, not
  claimed as an independently repeated native desktop check.

Native dialogs, real on-screen visual/accessibility behavior, installed-font
rendering, and high-DPI behavior remain unverified. No fixes, Git writes, or
publication were performed.
