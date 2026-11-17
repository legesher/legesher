"""Feature stories for the docs site's What's New pages.

A story is one directory under docs/stories/<id>/ describing one new or changed
feature: story.yml (identity, prose in the page languages, the steps a player
runs), sample.py (the sample in Python's own keywords), output.txt (what the
sample prints), and for each language with hand-written names and strings a
words.<lang>.yml plus the output.<lang>.txt that sample prints in that language.

This module loads and validates stories. The docs generator turns them into
per-language variants (generate_snippets.py), and reproduce_stories.py checks
that each variant's copied code prints its expected output with the released
Legesher.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from generate_snippets import _nfc

PAGE_LANGUAGES = ("en", "es", "ar")
# Hand-written names and strings exist for these languages only; every other
# language shows the engine's keywords with the sample's own names.
WORD_LIST_LANGUAGES = ("es", "ar")
BADGES = ("new", "improved")
SURFACES = ("playground", "editor", "command")
STEP_TYPES = frozenset(
    {
        "type",
        "run",
        "expect_output",
        "switch_language",
        "show_original",
        "highlight",
        "pause",
    }
)
EDITOR_STEP_TYPES = frozenset({"open_file", "hover", "open_panel", "pick_language"})
WORD_STATUSES = ("draft", "reviewed")
RELEASE_ID = re.compile(r"^rel-\d{8}-[a-z0-9-]+$")
STORY_KEYS = frozenset(
    {
        "id",
        "release",
        "package",
        "badge",
        "surface",
        "title",
        "why",
        "covers",
        "file_name",
        "steps",
    }
)


class StoryError(Exception):
    """A story that cannot be published as written. The message names the story and file."""


@dataclass(frozen=True)
class Words:
    names: dict[str, str]
    strings: dict[str, str]
    draft: bool


@dataclass(frozen=True)
class Story:
    id: str
    release: str | None
    package: str
    badge: str
    surface: str
    title: dict[str, str]
    why: dict[str, str]
    covers: list[str]
    file_name: str
    sample: str
    steps: list[tuple[str, str | None]]
    outputs: dict[str, str]
    words: dict[str, Words]
    path: Path


def _fail(story_dir: Path, file: str, message: str) -> StoryError:
    return StoryError(f"stories/{story_dir.name}/{file}: {message}")


def _read_yaml(story_dir: Path, file: str) -> dict:
    try:
        data = yaml.safe_load((story_dir / file).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise _fail(story_dir, file, "missing") from None
    except yaml.YAMLError as exc:
        raise _fail(story_dir, file, f"not valid YAML: {exc}") from None
    if not isinstance(data, dict):
        raise _fail(story_dir, file, "must be a mapping")
    return data


def _string_map(story_dir: Path, file: str, key: str, value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        raise _fail(story_dir, file, f"{key} must map strings to strings")
    return {_nfc(k): _nfc(v) for k, v in value.items()}


def _prose(story_dir: Path, key: str, value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(PAGE_LANGUAGES):
        raise _fail(
            story_dir, "story.yml", f"{key} needs exactly {', '.join(PAGE_LANGUAGES)}"
        )
    if not all(isinstance(v, str) and v.strip() for v in value.values()):
        raise _fail(story_dir, "story.yml", f"{key} entries must be non-empty text")
    return {lang: _nfc(value[lang]) for lang in PAGE_LANGUAGES}


def _steps(
    story_dir: Path, value: object, surface: str
) -> list[tuple[str, str | None]]:
    if not isinstance(value, list) or not value:
        raise _fail(story_dir, "story.yml", "steps must be a non-empty list")
    allowed = STEP_TYPES | (EDITOR_STEP_TYPES if surface == "editor" else frozenset())
    steps: list[tuple[str, str | None]] = []
    for step in value:
        if isinstance(step, str):
            kind, arg = step, None
        elif isinstance(step, dict) and len(step) == 1:
            ((kind, arg),) = step.items()
            if not isinstance(arg, str):
                raise _fail(
                    story_dir,
                    "story.yml",
                    f"step {kind}: its argument must be a string",
                )
            arg = _nfc(arg)
        else:
            raise _fail(
                story_dir,
                "story.yml",
                f"step {step!r} must be a word or a one-key mapping",
            )
        if kind not in allowed:
            where = " outside an editor story" if kind in EDITOR_STEP_TYPES else ""
            raise _fail(story_dir, "story.yml", f"unknown step {kind!r}{where}")
        steps.append((kind, arg))
    return steps


def _output(story_dir: Path, file: str) -> str:
    path = story_dir / file
    if not path.is_file():
        raise _fail(story_dir, file, "missing; it is what the sample must print")
    raw = path.read_bytes()
    if b"\r" in raw:
        raise _fail(story_dir, file, "has Windows line endings; a run prints \\n")
    text = raw.decode("utf-8")
    if not text.endswith("\n"):
        raise _fail(story_dir, file, "must end with a newline, as printed output does")
    return _nfc(text)


def _words(story_dir: Path, file: str) -> Words:
    data = _read_yaml(story_dir, file)
    unknown = set(data) - {"status", "names", "strings"}
    if unknown:
        raise _fail(story_dir, file, f"unknown keys: {', '.join(sorted(unknown))}")
    status = data.get("status")
    if status not in WORD_STATUSES:
        raise _fail(
            story_dir, file, f"status must be one of {', '.join(WORD_STATUSES)}"
        )
    return Words(
        names=_string_map(story_dir, file, "names", data.get("names")),
        strings=_string_map(story_dir, file, "strings", data.get("strings")),
        draft=status == "draft",
    )


def load_story(story_dir: Path) -> Story:
    """Load and validate one story directory. Raises StoryError naming the file at fault."""
    data = _read_yaml(story_dir, "story.yml")
    missing, unknown = STORY_KEYS - set(data), set(data) - STORY_KEYS
    if missing or unknown:
        parts = [f"missing {', '.join(sorted(missing))}"] if missing else []
        parts += [f"unknown {', '.join(sorted(unknown))}"] if unknown else []
        raise _fail(story_dir, "story.yml", "; ".join(parts))
    if data["id"] != story_dir.name:
        raise _fail(
            story_dir, "story.yml", f"id {data['id']!r} must equal the directory name"
        )
    release = data["release"]
    if release is not None and not (
        isinstance(release, str) and RELEASE_ID.match(release)
    ):
        raise _fail(
            story_dir,
            "story.yml",
            f"release {release!r} must be null or rel-YYYYMMDD-<slug>",
        )
    if not isinstance(data["package"], str) or not data["package"].strip():
        raise _fail(story_dir, "story.yml", "package must name the package and version")
    if data["badge"] not in BADGES:
        raise _fail(story_dir, "story.yml", f"badge must be one of {', '.join(BADGES)}")
    surface = data["surface"]
    if surface not in SURFACES:
        raise _fail(
            story_dir, "story.yml", f"surface must be one of {', '.join(SURFACES)}"
        )
    covers = data["covers"]
    if not isinstance(covers, list) or not all(isinstance(c, str) for c in covers):
        raise _fail(story_dir, "story.yml", "covers must be a list of text")
    file_name = data["file_name"]
    if (
        not isinstance(file_name, str)
        or "/" in file_name
        or not file_name.endswith(".py")
    ):
        raise _fail(
            story_dir, "story.yml", "file_name must be a plain name ending in .py"
        )

    try:
        sample = _nfc((story_dir / "sample.py").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise _fail(story_dir, "sample.py", "missing") from None
    try:
        ast.parse(sample)
    except SyntaxError as exc:
        raise _fail(
            story_dir, "sample.py", f"is not valid English Python: {exc}"
        ) from None

    words: dict[str, Words] = {}
    for path in sorted(story_dir.glob("words.*.yml")):
        lang = path.name[len("words.") : -len(".yml")]
        if lang not in WORD_LIST_LANGUAGES:
            raise _fail(
                story_dir,
                path.name,
                f"word lists exist for {', '.join(WORD_LIST_LANGUAGES)} only",
            )
        words[lang] = _words(story_dir, path.name)

    outputs: dict[str, str] = {}
    if surface != "editor":
        outputs["en"] = _output(story_dir, "output.txt")
        for lang in words:
            outputs[lang] = _output(story_dir, f"output.{lang}.txt")

    return Story(
        id=data["id"],
        release=release,
        package=_nfc(data["package"]),
        badge=data["badge"],
        surface=surface,
        title=_prose(story_dir, "title", data["title"]),
        why=_prose(story_dir, "why", data["why"]),
        covers=[_nfc(c) for c in covers],
        file_name=file_name,
        sample=sample,
        steps=_steps(story_dir, data["steps"], surface),
        outputs=outputs,
        words=words,
        path=story_dir,
    )


def load_stories(stories_dir: Path) -> list[Story]:
    """Every story under stories_dir, sorted by id; none when the directory is absent."""
    if not stories_dir.is_dir():
        return []
    return sorted(
        (
            load_story(d)
            for d in stories_dir.iterdir()
            if d.is_dir() and (d / "story.yml").exists()
        ),
        key=lambda s: s.id,
    )
