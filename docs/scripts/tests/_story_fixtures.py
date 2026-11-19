"""Copies of the fixture stories, edited one thing at a time, for the story tests."""

import shutil
from pathlib import Path

import yaml

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "stories"


def copy_story(
    tmp_path: Path, name: str, edit=None, source: str = "ok-playground"
) -> Path:
    """Copy a fixture story to tmp_path/<name>, set its id to <name>, apply edit(story_yml_dict)."""
    target = tmp_path / name
    shutil.copytree(FIXTURES / source, target)
    path = target / "story.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["id"] = name
    if edit:
        edit(data)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return target


def edit_words(story_dir: Path, lang: str, edit) -> None:
    """Apply edit(words_dict) to story_dir/words.<lang>.yml."""
    path = story_dir / f"words.{lang}.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    edit(data)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
