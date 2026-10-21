import csv

import pytest
from mseval import run as m


def test_prompts_load_and_have_all_languages():
    rows = m.load_prompts("prompts.csv")
    assert len(rows) >= 5
    assert all(r[l] for r in rows for l in m.LANGS)


def test_dry_run_writes_files(tmp_path):
    m.main(["--dry-run", "--out-dir", str(tmp_path)])
    files = sorted(p.name for p in tmp_path.iterdir())
    assert len(files) == 2
    resp = next(p for p in tmp_path.iterdir() if p.name.startswith("responses_"))
    rows = list(csv.DictReader(open(resp, encoding="utf-8")))
    assert len(rows) == len(m.load_prompts("prompts.csv")) * 3
    assert all(r["error"] == "" for r in rows)


def test_errors_are_recorded_not_raised():
    def boom(*a):
        raise RuntimeError("fail")
    rows = m.run([{"id": "x", "category": "c", "en": "hi"}], ["en"], "m", boom)
    assert rows[0]["error"] == "fail"


def test_unknown_language_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        m.main(["--dry-run", "--langs", "en,fr", "--out-dir", str(tmp_path)])
    assert list(tmp_path.iterdir()) == []


def test_duplicate_prompt_ids_are_rejected(tmp_path):
    path = tmp_path / "prompts.csv"
    path.write_text("id,category,en,ro,ru\n"
                    "p01,c,hi,salut,privet\n"
                    "p01,c,bye,pa,poka\n", encoding="utf-8")
    with pytest.raises(ValueError, match="more than once"):
        m.load_prompts(str(path))
