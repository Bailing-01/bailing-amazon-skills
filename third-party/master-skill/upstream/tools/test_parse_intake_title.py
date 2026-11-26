#!/usr/bin/env python3
"""Validator tests for the title field in parse_intake().

Run: python3 tools/test_parse_intake_title.py
Exits non-zero if any case fails.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill_writer import parse_intake, SkillWriterError


def _write(td, **extra):
    p = Path(td) / "intake.json"
    data = {
        "industry": "test",
        "slug": "test",
        "locale": "zh-CN",
        "profile": "practitioner",
    }
    data.update(extra)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_accepts_valid_title():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="红队渗透")
        data = parse_intake(p)
        assert data["title"] == "红队渗透"


def test_accepts_max_12_codepoint():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="LLM agent 基建")  # exactly 12
        data = parse_intake(p)
        assert len(data["title"]) == 12


def test_accepts_min_4_codepoint():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="中医诊疗")  # exactly 4
        data = parse_intake(p)
        assert len(data["title"]) == 4


def test_rejects_too_long_title():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="这是一个超过十二字的标题示例abc")  # 16
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "outside 4-12" in str(e), f"wrong error msg: {e}"
            return
        raise AssertionError("expected SkillWriterError for too-long title")


def test_rejects_too_short_title():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="中医")  # 2
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "outside 4-12" in str(e)
            return
        raise AssertionError("expected SkillWriterError for too-short title")


def test_rejects_parens():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="中医诊疗(临床)")
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "banned chars" in str(e)
            return
        raise AssertionError("expected SkillWriterError for parens")


def test_rejects_em_dash():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="中医—诊疗")
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "banned chars" in str(e)
            return
        raise AssertionError("expected SkillWriterError for em-dash")


def test_rejects_slash():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title="中医/西医")
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "banned chars" in str(e)
            return
        raise AssertionError("expected SkillWriterError for slash")


def test_rejects_non_string_title():
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, title=42)
        try:
            parse_intake(p)
        except SkillWriterError as e:
            assert "must be a string" in str(e)
            return
        raise AssertionError("expected SkillWriterError for non-string title")


def test_missing_title_is_ok():
    # Backward-compat: validator treats title as optional.
    # The Phase 0 prompt is what makes it required for new runs.
    with tempfile.TemporaryDirectory() as td:
        p = _write(td)  # no title
        data = parse_intake(p)
        assert data.get("title") is None


def main():
    tests = [
        test_accepts_valid_title,
        test_accepts_max_12_codepoint,
        test_accepts_min_4_codepoint,
        test_rejects_too_long_title,
        test_rejects_too_short_title,
        test_rejects_parens,
        test_rejects_em_dash,
        test_rejects_slash,
        test_rejects_non_string_title,
        test_missing_title_is_ok,
    ]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"FAIL  {t.__name__} — {e}")
    print(f"\n{passed}/{len(tests)} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
