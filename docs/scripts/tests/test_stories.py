import shutil
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stories import StoryError, load_stories, load_story  # noqa: E402

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


def refused(story_dir: Path, file: str):
    return pytest.raises(StoryError, match=rf"^stories/{story_dir.name}/{file}: ")


def test_loads_the_fixture_story():
    s = load_story(FIXTURES / "ok-playground")
    assert s.surface == "playground" and s.file_name == "divide.py"
    assert set(s.title) == {"en", "es", "ar"}
    assert s.steps[0] == ("type", None) and ("pause", "800") in s.steps
    assert s.outputs["en"].endswith("\n") and s.words["ar"].draft is True
    assert s.words["ar"].names["divide"] == "اقسم"
    assert s.words["es"].strings['"by zero"'] == '"entre cero"'
    assert s.outputs["ar"].startswith("محاولة قسمة 10 على 2\n")


def test_id_must_equal_directory_name(tmp_path):
    d = copy_story(tmp_path, "renamed", edit=lambda s: s.update(id="something-else"))
    with refused(d, "story.yml"):
        load_story(d)


def test_missing_page_language_in_title_is_refused(tmp_path):
    d = copy_story(tmp_path, "no-arabic-title", edit=lambda s: s["title"].pop("ar"))
    with refused(d, "story.yml"):
        load_story(d)


def test_unknown_step_is_refused(tmp_path):
    d = copy_story(tmp_path, "dance", edit=lambda s: s.update(steps=["dance"]))
    with refused(d, "story.yml"):
        load_story(d)


def test_editor_step_outside_editor_story_is_refused(tmp_path):
    d = copy_story(
        tmp_path,
        "hover-in-playground",
        edit=lambda s: s["steps"].append({"hover": "def"}),
    )
    with refused(d, "story.yml"):
        load_story(d)


def test_bad_release_id_is_refused(tmp_path):
    d = copy_story(tmp_path, "bad-release", edit=lambda s: s.update(release="v2"))
    with refused(d, "story.yml"):
        load_story(d)


def test_good_release_id_is_kept(tmp_path):
    d = copy_story(
        tmp_path,
        "good-release",
        edit=lambda s: s.update(release="rel-20261212-legesher-v2"),
    )
    assert load_story(d).release == "rel-20261212-legesher-v2"


def test_output_with_crlf_is_refused(tmp_path):
    d = copy_story(tmp_path, "crlf")
    (d / "output.txt").write_bytes(
        (d / "output.txt").read_bytes().replace(b"\n", b"\r\n")
    )
    with refused(d, "output.txt"):
        load_story(d)


def test_output_without_final_newline_is_refused(tmp_path):
    d = copy_story(tmp_path, "no-final-newline")
    (d / "output.ar.txt").write_text(
        (d / "output.ar.txt").read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8"
    )
    with refused(d, "output.ar.txt"):
        load_story(d)


def test_word_list_without_output_is_refused(tmp_path):
    d = copy_story(tmp_path, "words-without-output")
    (d / "output.es.txt").unlink()
    with refused(d, "output.es.txt"):
        load_story(d)


def test_word_list_without_status_is_refused(tmp_path):
    d = copy_story(tmp_path, "no-status")
    words = yaml.safe_load((d / "words.ar.yml").read_text(encoding="utf-8"))
    words.pop("status")
    (d / "words.ar.yml").write_text(
        yaml.safe_dump(words, allow_unicode=True), encoding="utf-8"
    )
    with refused(d, "words.ar.yml"):
        load_story(d)


def test_sample_that_is_not_python_is_refused(tmp_path):
    d = copy_story(tmp_path, "broken-sample")
    (d / "sample.py").write_text("def broken(:\n", encoding="utf-8")
    with refused(d, "sample.py"):
        load_story(d)


def test_playground_story_needs_output(tmp_path):
    d = copy_story(tmp_path, "no-output")
    (d / "output.txt").unlink()
    with refused(d, "output.txt"):
        load_story(d)


def test_editor_story_needs_no_output():
    s = load_story(FIXTURES / "ok-editor")
    assert s.outputs == {} and s.words == {}
    assert ("hover", "def") in s.steps


def test_text_is_nfc_normalized(tmp_path):
    decomposed = "Manejo de errores con tus palabras: se intentó"
    d = copy_story(
        tmp_path, "nfd-title", edit=lambda s: s["title"].update(es=decomposed)
    )
    assert load_story(d).title["es"].endswith("intentó")


def test_load_stories_is_sorted_and_tolerates_absent_dir(tmp_path):
    assert load_stories(tmp_path / "none") == []
    copy_story(tmp_path, "zeta")
    copy_story(tmp_path, "alpha")
    assert [s.id for s in load_stories(tmp_path)] == ["alpha", "zeta"]
