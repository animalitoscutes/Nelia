"""
Configuration and Industry Standards for Screenplay and Novel Studio.
Follows standard Hollywood Screenplay margin rules (AMPAS / WGA / Final Draft)
and Scrivener / Ulysses long-form narrative conventions.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

class ScriptElementType:
    SCENE_HEADING = "SCENE_HEADING"
    ACTION = "ACTION"
    CHARACTER = "CHARACTER"
    PARENTHETICAL = "PARENTHETICAL"
    DIALOGUE = "DIALOGUE"
    TRANSITION = "TRANSITION"
    SHOT = "SHOT"
    NOTE = "NOTE"

@dataclass
class ElementFormatting:
    name: str
    code: str
    left_indent_inches: float      # Standard screenplay measurements (8.5 x 11 inch US Letter)
    right_indent_inches: float
    space_before_lines: float      # Blank lines or spacing before element
    space_after_lines: float
    all_caps: bool
    shortcut_hint: str

# Standard industry dimensions (1 inch = 72 pt or approx 10 chars at 12pt Courier)
# Margins relative to the 8.5" page width with 1.5" left margin base:
FORMAT_RULES: Dict[str, ElementFormatting] = {
    ScriptElementType.SCENE_HEADING: ElementFormatting(
        name="Scene Heading",
        code=ScriptElementType.SCENE_HEADING,
        left_indent_inches=0.0,    # Base 1.5"
        right_indent_inches=1.0,
        space_before_lines=2.0,
        space_after_lines=1.0,
        all_caps=True,
        shortcut_hint="Ctrl+1"
    ),
    ScriptElementType.ACTION: ElementFormatting(
        name="Action",
        code=ScriptElementType.ACTION,
        left_indent_inches=0.0,
        right_indent_inches=1.0,
        space_before_lines=1.0,
        space_after_lines=1.0,
        all_caps=False,
        shortcut_hint="Ctrl+2"
    ),
    ScriptElementType.CHARACTER: ElementFormatting(
        name="Character",
        code=ScriptElementType.CHARACTER,
        left_indent_inches=2.2,    # ~3.7" from page left
        right_indent_inches=1.5,
        space_before_lines=1.0,
        space_after_lines=0.0,
        all_caps=True,
        shortcut_hint="Ctrl+3 / Tab"
    ),
    ScriptElementType.PARENTHETICAL: ElementFormatting(
        name="Parenthetical",
        code=ScriptElementType.PARENTHETICAL,
        left_indent_inches=1.6,    # ~3.1" from page left
        right_indent_inches=2.0,
        space_before_lines=0.0,
        space_after_lines=0.0,
        all_caps=False,
        shortcut_hint="Ctrl+4 / Tab"
    ),
    ScriptElementType.DIALOGUE: ElementFormatting(
        name="Dialogue",
        code=ScriptElementType.DIALOGUE,
        left_indent_inches=1.0,    # ~2.5" from page left
        right_indent_inches=1.5,
        space_before_lines=0.0,
        space_after_lines=1.0,
        all_caps=False,
        shortcut_hint="Ctrl+5 / Enter"
    ),
    ScriptElementType.TRANSITION: ElementFormatting(
        name="Transition",
        code=ScriptElementType.TRANSITION,
        left_indent_inches=4.0,    # ~5.5" to 6.0" from page left
        right_indent_inches=0.0,
        space_before_lines=1.0,
        space_after_lines=2.0,
        all_caps=True,
        shortcut_hint="Ctrl+6"
    ),
    ScriptElementType.SHOT: ElementFormatting(
        name="Shot",
        code=ScriptElementType.SHOT,
        left_indent_inches=0.0,
        right_indent_inches=1.0,
        space_before_lines=1.0,
        space_after_lines=1.0,
        all_caps=True,
        shortcut_hint="Ctrl+7"
    ),
}

# The Holy Grail: The Enter & Tab Transition Matrix (Industry Standard Muscle Memory)
ENTER_TRANSITIONS = {
    ScriptElementType.SCENE_HEADING: ScriptElementType.ACTION,
    ScriptElementType.ACTION: ScriptElementType.ACTION,
    ScriptElementType.CHARACTER: ScriptElementType.DIALOGUE,
    ScriptElementType.PARENTHETICAL: ScriptElementType.DIALOGUE,
    ScriptElementType.DIALOGUE: ScriptElementType.ACTION,
    ScriptElementType.TRANSITION: ScriptElementType.SCENE_HEADING,
    ScriptElementType.SHOT: ScriptElementType.ACTION,
}

TAB_TRANSITIONS = {
    ScriptElementType.ACTION: ScriptElementType.CHARACTER,
    ScriptElementType.CHARACTER: ScriptElementType.TRANSITION,
    ScriptElementType.DIALOGUE: ScriptElementType.PARENTHETICAL,
    ScriptElementType.PARENTHETICAL: ScriptElementType.DIALOGUE,
    ScriptElementType.TRANSITION: ScriptElementType.SCENE_HEADING,
}

# Scene heading prefixes for smart auto-completion
SCENE_PREFIXES = [
    "INT.",
    "EXT.",
    "INT./EXT.",
    "I/E.",
    "EXT./INT.",
    "EST.",
]

SCENE_TIMES = [
    "DAY",
    "NIGHT",
    "DAWN",
    "DUSK",
    "CONTINUOUS",
    "LATER",
    "MOMENTS LATER",
    "SAME TIME",
]

DEFAULT_SETTINGS = {
    "app_title": "NELIA | Pro Screenplay & Novel Studio",
    "screenplay_font_family": "Courier Prime",
    "screenplay_font_size": 12,
    "novel_font_family": "Merriweather",
    "novel_font_size": 13,
    "ui_font_family": "Inter",
    "ui_font_size": 10,
    "target_words_per_day": 1500,
    "typewriter_scrolling": True,
}
