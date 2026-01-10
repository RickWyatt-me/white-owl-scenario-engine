from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


DIRECTIVES_DIR = "directives"


@dataclass
class Directive:
    """
    Represents a single directive (SOP) loaded from markdown.
    """
    name: str
    filename: str
    content: str


def list_directive_files() -> List[str]:
    """
    Return a list of .md files in the directives directory.
    """
    if not os.path.isdir(DIRECTIVES_DIR):
        raise FileNotFoundError(
            f"Directives directory '{DIRECTIVES_DIR}' not found."
        )

    return sorted(
        f for f in os.listdir(DIRECTIVES_DIR)
        if f.endswith(".md")
    )


def load_directive(filename: str) -> Directive:
    """
    Load a single directive by filename.
    """
    path = os.path.join(DIRECTIVES_DIR, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Directive file not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"Directive '{filename}' is empty.")

    name = filename.replace(".md", "")

    return Directive(
        name=name,
        filename=filename,
        content=content,
    )


def load_all_directives() -> Dict[str, Directive]:
    """
    Load all directives into a dict keyed by directive name.
    """
    directives: Dict[str, Directive] = {}

    for filename in list_directive_files():
        directive = load_directive(filename)
        directives[directive.name] = directive

    return directives


def get_directive_or_fail(name: str) -> Directive:
    """
    Convenience accessor with explicit failure.
    """
    directives = load_all_directives()

    if name not in directives:
        available = ", ".join(sorted(directives.keys()))
        raise KeyError(
            f"Directive '{name}' not found. "
            f"Available directives: {available}"
        )

    return directives[name]
