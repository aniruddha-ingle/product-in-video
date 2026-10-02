"""Timeline contract v0: load/dump round trips, version refusal, unknown fields, audio."""

import json

import pytest

from piv.timeline import (
    FormatError,
    Recipe,
    Timeline,
    ValidationError,
    VersionError,
    build_timeline,
    canonical_json,
    dump,
    dumps,
    load,
    load_recipe,
    loads,
)
from piv.timeline.recipes import BASE_NAMES, scaled_path
from piv.timeline.synthetic import synthetic_template

HOOK = "HOOK LINE\nSECOND LINE"


@pytest.fixture(scope="module")
def timeline() -> Timeline:
    return build_timeline(load_recipe("build-up"), synthetic_template(), "9:16", headline=HOOK)


def _doc(tl: Timeline) -> dict:
    return json.loads(dumps(tl))


@pytest.mark.parametrize("name", BASE_NAMES)
@pytest.mark.parametrize("duration_ms", [8000, 6000])
def test_recipe_round_trip(name, duration_ms):
    r = load_recipe(name, duration_ms)
    again = loads(dumps(r))
    assert isinstance(again, Recipe)
    assert again == r
    assert dumps(again) == dumps(r)


def test_timeline_round_trip(timeline, tmp_path):
    path = tmp_path / "t.json"
    dump(timeline, path)
    again = load(path)
    assert again == timeline
    assert canonical_json(again.to_json()) == canonical_json(timeline.to_json())
    assert not list(tmp_path.glob("*.tmp"))  # atomic write leaves nothing behind


def test_recipe_files_are_already_in_dump_form():
    for name in BASE_NAMES:
        path = scaled_path(name, 6000)
        assert path.read_text() == dumps(loads(path.read_text()))


@pytest.mark.parametrize("version", [1, 2, -1, "0", 0.0, True, None])
def test_unknown_format_version_is_refused(timeline, version):
    d = _doc(timeline)
    d["format_version"] = version
    with pytest.raises((VersionError, FormatError)) as e:
        loads(json.dumps(d))
    if type(version) is int:  # a well-typed but unknown version
        assert isinstance(e.value, VersionError)
        assert "refusing" in str(e.value)


def test_missing_format_version_is_refused(timeline):
    d = _doc(timeline)
    del d["format_version"]
    with pytest.raises(FormatError, match="format_version"):
        loads(json.dumps(d))


def test_wrong_kind_is_refused(timeline):
    with pytest.raises(FormatError, match="recipe"):
        loads(dumps(timeline), kind="recipe")


def test_unknown_optional_fields_are_ignored_and_kept(timeline):
    d = _doc(timeline)
    d["future_top_level"] = {"x": 1}
    d["tracks"]["video"][1]["future_layer_field"] = "kept"
    d["tracks"]["video"][1]["transform"]["future_tr"] = 3
    d["tracks"]["text"][0]["runs"][0]["future_run"] = [1, 2]
    d["tracks"]["future_track"] = []
    tl = loads(json.dumps(d))
    assert tl.extra == {"future_top_level": {"x": 1}}
    assert tl.tracks.video[1].extra == {"future_layer_field": "kept"}
    out = json.loads(dumps(tl))
    assert out["future_top_level"] == {"x": 1}
    assert out["tracks"]["video"][1]["future_layer_field"] == "kept"
    assert out["tracks"]["video"][1]["transform"]["future_tr"] == 3
    assert out["tracks"]["text"][0]["runs"][0]["future_run"] == [1, 2]
    assert out["tracks"]["future_track"] == []


def test_audio_track_must_exist(timeline):
    d = _doc(timeline)
    del d["tracks"]["audio"]
    with pytest.raises(FormatError, match="audio"):
        loads(json.dumps(d))


def test_audio_must_be_empty_in_v0(timeline):
    d = _doc(timeline)
    d["tracks"]["audio"] = [{"kind": "music", "src": "x.wav"}]
    with pytest.raises(ValidationError, match="audio must be empty"):
        loads(json.dumps(d))


def test_recipe_audio_must_be_empty_too():
    d = load_recipe("build-up").to_json()
    d["tracks"]["audio"] = [{"kind": "voice"}]
    with pytest.raises(ValidationError, match="audio must be empty"):
        loads(json.dumps(d))


def test_built_timelines_have_empty_audio():
    for ratio in ("4:5", "1:1", "9:16"):
        tl = build_timeline(
            load_recipe("details-first", 6000),
            synthetic_template(),
            ratio,
            headline=HOOK,
        )
        assert tl.tracks.audio == ()
        assert _doc(tl)["tracks"]["audio"] == []


def test_load_without_validation_still_checks_version(timeline):
    d = _doc(timeline)
    d["tracks"]["audio"] = [{"kind": "music"}]
    assert loads(json.dumps(d), validate=False).tracks.audio  # loads, unvalidated
    d["format_version"] = 1
    with pytest.raises(VersionError):
        loads(json.dumps(d), validate=False)


def test_bad_types_are_format_errors(timeline):
    d = _doc(timeline)
    d["fps"] = 29.97
    with pytest.raises(FormatError, match="fps"):
        loads(json.dumps(d))
    d = _doc(timeline)
    d["tracks"]["video"][1]["transform"]["scale"] = [{"t_ms": 0.5, "v": 1}]
    with pytest.raises(FormatError, match="t_ms"):
        loads(json.dumps(d))
