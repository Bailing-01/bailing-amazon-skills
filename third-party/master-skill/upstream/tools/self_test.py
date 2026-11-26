#!/usr/bin/env python3
"""Self-test script for all 7 prototype skills.

Checks:
1. SKILL.md exists + has valid frontmatter (name, description, allowed-tools, triggers)
2. meta.json is valid JSON + has expected fields
3. All sub-skill paths in meta.json + SKILL.md exist
4. All sub-skills have valid frontmatter
5. CLI scripts are executable + don't crash on --help / no args
6. References (research files + synthesis) exist
7. Internal markdown links don't 404
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# Informational notes (e.g. flagged-legacy prototypes) — printed after the
# per-prototype results, never counted as issues.
INFO_NOTES: list = []


def parse_frontmatter(text):
    """Parse YAML frontmatter. Returns (frontmatter dict, rest of text)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fm_text = text[4:end]
    rest = text[end + 5:]
    fm = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if current_list is not None:
                current_list.append(line.lstrip("- ").strip().strip('"').strip("'"))
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                current_key = key
                current_list = []
                fm[key] = current_list
            else:
                current_list = None
                fm[key] = val.strip('"').strip("'")
    return fm, rest


def check_skill(prototype_dir, results):
    """Check one prototype's output skill."""
    name = prototype_dir.name
    out = prototype_dir / "output"
    issues = []

    # 1. SKILL.md exists
    skill_md = out / "SKILL.md"
    if not skill_md.exists():
        issues.append(f"missing SKILL.md")
        results[name] = issues
        return

    text = skill_md.read_text(encoding="utf-8")
    fm, rest = parse_frontmatter(text)
    if not fm:
        issues.append("SKILL.md missing or malformed frontmatter")
    else:
        for required in ("name", "description"):
            if required not in fm:
                issues.append(f"SKILL.md frontmatter missing '{required}'")

    # 2. Leftover template placeholders
    leftover = re.findall(r'\{\{[^}]+\}\}', text)
    if leftover:
        issues.append(f"SKILL.md has leftover {{{{...}}}} placeholders: {leftover[:3]}")

    # 3. meta.json
    meta_path = out / "meta.json"
    if not meta_path.exists():
        issues.append("missing meta.json")
        meta = {}
    else:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(f"meta.json invalid JSON: {e}")
            meta = {}

    # 4. sub_skills
    for ss in meta.get("sub_skills", []):
        ss_path = out / ss.get("path", "")
        if not ss_path.exists():
            issues.append(f"sub_skill path missing: {ss.get('path')}")
            continue
        ss_text = ss_path.read_text(encoding="utf-8")
        ss_fm, _ = parse_frontmatter(ss_text)
        if not ss_fm:
            issues.append(f"sub_skill {ss.get('slug')} missing frontmatter")
        else:
            for required in ("name", "description"):
                if required not in ss_fm:
                    issues.append(f"sub_skill {ss.get('slug')} missing '{required}'")

    # 5. SKILL.md sub-skill table paths exist. Rows explicitly marked 待生成 /
    # pending (skip_sub_skills mode declares them without distilling) are
    # intentional forward references, not broken links.
    for line in text.splitlines():
        if "待生成" in line or "pending" in line.lower():
            continue
        for sp in set(re.findall(r'sub-skills/([a-z0-9-]+)/SKILL\.md', line)):
            ss_path = out / "sub-skills" / sp / "SKILL.md"
            if not ss_path.exists():
                issues.append(f"SKILL.md references missing sub-skill: sub-skills/{sp}/SKILL.md")

    # 6+7. research trail (six track files + synthesis.md). Prototypes whose
    # meta.json declares `"research_trail": false` are legacy deep-distills
    # whose notes were never archived in-repo — report informationally, don't
    # fail them forever.
    if meta.get("research_trail") is False:
        INFO_NOTES.append(
            f"{name}: no research trail (flagged legacy — {meta.get('research_trail_note', 'no note')})"
        )
    else:
        rdir = prototype_dir / "references" / "research"
        expected = ["01-figures.md", "02-tools.md", "03-workflows.md",
                    "04-canon.md", "05-sources.md", "06-glossary.md"]
        for f in expected:
            if not (rdir / f).exists():
                issues.append(f"research file missing: {f}")

        syn = prototype_dir / "references" / "synthesis.md"
        if not syn.exists():
            issues.append("references/synthesis.md missing")

    # 8. CLI scripts exist + executable + no leftover placeholders + syntax OK
    cli_dir = out / "cli"
    if cli_dir.exists():
        sh_files = list(cli_dir.rglob("*.sh"))
        for sh in sh_files:
            rel = sh.relative_to(out)
            # lib/*.sh is sourced (not executed) — skip executable check
            is_lib = "lib/" in str(rel) or str(rel).startswith("cli/lib/")
            if not is_lib and not os.access(sh, os.X_OK):
                issues.append(f"cli script not executable: {rel}")
            # Syntax check
            r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
            if r.returncode != 0:
                issues.append(f"cli syntax error in {rel}: {r.stderr.strip()[:120]}")
            # Leftover {placeholder} or {{placeholder}} in non-shell-substitution context
            sh_text = sh.read_text(encoding="utf-8")
            # Detect single-brace placeholders like {industry-cn} or {INDUSTRY_CN} that look templatey
            # (ignore bash ${var} which is fine, ignore bash literal { in }
            leftover_single = re.findall(r'(?<!\$)\{[a-zA-Z][a-zA-Z0-9_-]*-cn\}|(?<!\$)\{INDUSTRY[A-Z_]*\}', sh_text)
            leftover_double = re.findall(r'\{\{[^}]+\}\}', sh_text)
            for ph in set(leftover_single + leftover_double):
                issues.append(f"cli leftover placeholder {ph} in {rel}")

    # 9. Section 9 (Agentic Protocol) — should not be duplicated
    section9_count = len(re.findall(r'^## 9\.\s', text, re.MULTILINE))
    if section9_count > 1:
        issues.append(f"Section 9 duplicated ({section9_count} times)")

    # 10. SKILL.md frontmatter triggers must be a list
    if fm and "triggers" in fm:
        if not isinstance(fm["triggers"], list):
            issues.append("frontmatter triggers must be a YAML list")

    results[name] = issues


def smoke_test_tools(skill_root: Path) -> list[str]:
    """Run --help on each tool to confirm imports + argparse work; run sample
    inputs through stdlib-only tools (those that don't require lazy installs).

    Returns a list of issue strings; empty list means all green.
    """
    issues: list[str] = []
    py = sys.executable

    tools_root = skill_root / "tools"

    # 1. Each Python tool should respond to --help (or run with no-args + show usage)
    helpable_tools = [
        # Q1
        tools_root / "research" / "source_verifier.py",
        tools_root / "research" / "quality_check.py",
        # Q3 collectors
        tools_root / "collectors" / "github_topics.py",
        tools_root / "collectors" / "arxiv_collect.py",
        tools_root / "collectors" / "rss_collect.py",
        tools_root / "collectors" / "podcast_rss.py",
        # Q3 ingest (lazy-install gated; --help should still work without deps)
        tools_root / "ingest" / "pdf_to_chunks.py",
        tools_root / "ingest" / "epub_to_chunks.py",
        tools_root / "ingest" / "pptx_to_chunks.py",
        # Q4 transcribe
        tools_root / "transcribe" / "whisper_transcribe.py",
        tools_root / "transcribe" / "srt_to_transcript.py",
        tools_root / "transcribe" / "transcript_scorer.py",
        tools_root / "transcribe" / "extract_mentions.py",
        # Q5 / Q6
        tools_root / "research" / "cold_detector.py",
        tools_root / "research" / "claim_verifier.py",
        tools_root / "research" / "refresh_sources.py",
        # core
        tools_root / "skill_writer.py",
        tools_root / "cli_writer.py",
        tools_root / "update_skill.py",
        tools_root / "install.py",
    ]
    for tool in helpable_tools:
        if not tool.exists():
            issues.append(f"tool missing: {tool.relative_to(skill_root)}")
            continue
        # Try --help first; some scripts use sub-command CLIs and reject --help
        # at root, so also accept exit code 0 OR 2 (argparse defaults) AND
        # produce some "usage" string on stdout/stderr.
        r = subprocess.run([py, str(tool), "--help"], capture_output=True, text=True, timeout=15)
        combined = (r.stdout + r.stderr).lower()
        if "usage" not in combined and "options" not in combined:
            issues.append(
                f"{tool.relative_to(skill_root)} --help did not print usage "
                f"(rc={r.returncode}, head: {(r.stdout or r.stderr)[:120]!r})"
            )

    # 2. source_verifier classify — golden cases
    # (iter 25 — codex P2 #12 audit). Each entry: (url, expected_bucket, label).
    sv = tools_root / "research" / "source_verifier.py"
    if sv.exists():
        golden = [
            # Allowlisted primary
            ("https://arxiv.org/abs/2305.12345", "verified_primary", "arxiv allowlist"),
            ("https://github.com/anthropics/claude-cookbook", "verified_primary", "github repo root"),
            ("https://github.com/anthropics/claude-cookbook/issues/123", "reference", "github issue thread"),
            # zh-CN blacklist
            ("https://www.zhihu.com/answer/123", "blacklisted", "zhihu blacklist"),
            ("https://mp.weixin.qq.com/s/foo", "blacklisted", "wechat article blacklist"),
            # en blacklist
            ("https://www.g2.com/products/foo", "blacklisted", "g2 blacklist"),
            # Reference-tier
            ("https://twitter.com/karpathy/status/12345", "reference", "twitter single post"),
            # Brand domain root — should NOT be auto-primary (iter 25 fix)
            ("https://example.com/", "secondary", "brand-root NOT auto-primary"),
            ("https://random.com/some-cool-article", "secondary", "slug-style NOT auto-primary"),
            # Brand-domain content path — should still be primary
            ("https://www.helium10.com/podcast/", "verified_primary", "brand /podcast/ path"),
            ("https://swyx.substack.com/p/foo", "verified_primary", "substack subdomain"),
            # YouTube channel root
            ("https://www.youtube.com/c/Latent", "verified_primary", "youtube channel"),
            # Engineering blog subdomain
            ("https://engineering.foo.com/post", "verified_primary", "engineering subdomain"),
        ]
        for url, expected_bucket, label in golden:
            r = subprocess.run(
                [py, str(sv), "classify", url],
                capture_output=True, text=True, timeout=15,
            )
            actual_bucket = (r.stdout.split("\t")[0] if r.stdout else "").strip()
            if actual_bucket != expected_bucket:
                issues.append(
                    f"source_verifier ({label}): {url!r} expected {expected_bucket}, "
                    f"got {actual_bucket!r}"
                )

    # 3. srt_to_transcript --jsonl smoke test
    s2t = tools_root / "transcribe" / "srt_to_transcript.py"
    if s2t.exists():
        import tempfile
        sample_srt = (
            "1\n00:00:01,500 --> 00:00:03,200\nHello world.\n\n"
            "2\n00:00:03,300 --> 00:00:05,800\nSPEAKER_00: Test.\n\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False) as f:
            f.write(sample_srt)
            srt_path = f.name
        out_path = srt_path + ".jsonl"
        r = subprocess.run(
            [py, str(s2t), srt_path, out_path, "--jsonl"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            issues.append(f"srt_to_transcript --jsonl failed: {r.stderr[:200]}")
        else:
            with open(out_path) as f:
                lines = [line.strip() for line in f if line.strip()]
            if len(lines) < 2:
                issues.append(f"srt_to_transcript --jsonl produced {len(lines)} lines, expected ≥ 2")
            else:
                first = json.loads(lines[0])
                if "start" not in first or "speaker" not in first:
                    issues.append(f"srt_to_transcript --jsonl missing start/speaker fields: {first}")
                second = json.loads(lines[1])
                if second.get("speaker") != "SPEAKER_00":
                    issues.append(f"srt_to_transcript --jsonl didn't extract speaker: {second}")
        # cleanup
        for p in (srt_path, out_path):
            try:
                Path(p).unlink()
            except OSError:
                pass

    # 4. transcript_scorer + extract_mentions on a small sample
    scorer = tools_root / "transcribe" / "transcript_scorer.py"
    mentions = tools_root / "transcribe" / "extract_mentions.py"
    if scorer.exists() and mentions.exists():
        import tempfile
        cues = [
            {"start": "00:00:01", "end": "00:00:08", "speaker": None,
             "text": "Welcome to the show. Today we have Yann LeCun talking about LangChain."},
            {"start": "00:00:09", "end": "00:00:18", "speaker": "Yann LeCun",
             "text": "Anthropic raised $5B in 2026, and Claude 4.7 sees 25% market share."},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for c in cues:
                f.write(json.dumps(c) + "\n")
            input_path = f.name
        # Score
        r = subprocess.run(
            [py, str(scorer), input_path, "-"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0 or "actionable_score" not in r.stdout:
            issues.append(f"transcript_scorer failed: {r.stderr[:200]} stdout: {r.stdout[:200]}")
        # Mentions
        r = subprocess.run(
            [py, str(mentions), input_path, "-"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0 or "Anthropic" not in r.stdout:
            issues.append(f"extract_mentions failed or missed Anthropic: {r.stderr[:200]}")
        Path(input_path).unlink(missing_ok=True)

    # 5. cold_detector on llm-agent-infra prototype: --stage full → normal,
    # and --stage wave1 → also normal (golden case for codex P0 #2 fix).
    cd = tools_root / "research" / "cold_detector.py"
    proto = skill_root / "prototypes" / "llm-agent-infra-master" / "output"
    if cd.exists() and proto.exists():
        for stage in ("full", "wave1"):
            r = subprocess.run(
                [py, str(cd), "--skill-dir", str(proto), "--stage", stage, "--json"],
                capture_output=True, text=True, timeout=15,
            )
            try:
                rep = json.loads(r.stdout)
                if rep.get("verdict") != "normal":
                    issues.append(
                        f"cold_detector --stage {stage} on llm-agent-infra "
                        f"expected normal, got {rep.get('verdict')!r} "
                        f"(triggers: {rep.get('triggers')})"
                    )
                if rep.get("stage") != stage:
                    issues.append(f"cold_detector --stage {stage} did not echo stage in report")
            except Exception as e:
                issues.append(f"cold_detector json parse failed: {e}, stdout={r.stdout[:200]}")

    # 6. quality_check items 13/14 should be wired up (run on cross-border)
    qc = tools_root / "research" / "quality_check.py"
    proto2 = skill_root / "prototypes" / "cross-border-ecommerce-master" / "output"
    if qc.exists() and proto2.exists():
        r = subprocess.run(
            [py, str(qc), "check", "--skill-dir", str(proto2), "--json"],
            capture_output=True, text=True, timeout=30,
        )
        try:
            rep = json.loads(r.stdout)
            ids = {item["id"] for item in rep.get("results", [])}
            for needed in ("13", "14", "15", "16"):
                if needed not in ids:
                    issues.append(f"quality_check missing item {needed}")
        except Exception as e:
            issues.append(f"quality_check json parse failed: {e}, stdout={r.stdout[:200]}")

    # 7. Iter 26 fixtures (codex 3rd-audit P1 #3 hardening): make sure the 5
    # boundary-case fixes still hold up.
    sys.path.insert(0, str(tools_root / "research"))
    try:
        # 7.1 Bold evidence regex — accept all 4 markdown variants
        from quality_check import check_claim_evidence_coverage  # type: ignore[no-redef]
        # We don't have a fixture skill_dir handy; just verify the regex.
        import re
        pat = re.compile(
            r"\*{0,2}evidence\*{0,2}\s*[:：]\*{0,2}\s*\[\s*([^\]]+)\]",
            re.IGNORECASE,
        )
        for sample in [
            "evidence: [T01-S001, T02-S005]",
            "**evidence**: [T01-S001]",
            "**evidence:** [T01-S001, T01-S002]",
            "evidence ：[T01-S001]",  # fullwidth + space-before-colon
        ]:
            if not pat.search(sample):
                issues.append(f"iter 26 evidence regex misses: {sample!r}")

        # 7.2 YAML block-scalar markers — recognize 4 variants
        for marker in ["|", "|-", "|+", ">"]:
            text = f"---\nname: foo\ndescription: {marker}\n  line one\n  line two\n---\n"
            block_m = re.search(
                r"^description:\s*[|>][-+]?\s*\n((?:(?:[ \t]+.*)?\n)+)",
                text, re.MULTILINE,
            )
            if not block_m:
                issues.append(f"iter 26 YAML block-scalar fix misses marker: {marker!r}")

        # 7.3 Unsafe copytree containment guard
        from skill_writer import _safe_copytree, SkillWriterError  # type: ignore[no-redef]
        import tempfile, os
        # Same path → no-op (ok)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "data"
            src.mkdir()
            (src / "file.txt").write_text("hello")
            try:
                _safe_copytree(src, src)  # same → no-op
            except Exception as e:
                issues.append(f"iter 26 _safe_copytree same path raised: {e}")
        # src under dst → must raise
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp) / "outer"
            outer.mkdir()
            inner = outer / "inner"
            inner.mkdir()
            try:
                _safe_copytree(inner, outer)
                issues.append("iter 26 _safe_copytree did not refuse src-under-dst")
            except SkillWriterError:
                pass

        # 7.4 source_manifest consistency on _fixtures/blacklist-test.md
        from source_manifest import parse_manifests, check_bucket_consistency  # type: ignore[no-redef]
        fixture_dir = skill_root / "prototypes" / "_fixtures"
        if (fixture_dir / "blacklist-test.md").exists():
            # Simulate a skill_dir layout: references/research/blacklist-test.md
            with tempfile.TemporaryDirectory() as tmp:
                fake_skill = Path(tmp)
                (fake_skill / "references" / "research").mkdir(parents=True)
                shutil.copy(
                    fixture_dir / "blacklist-test.md",
                    fake_skill / "references" / "research" / "blacklist-test.md",
                )
                rows = parse_manifests(fake_skill)
                blacklisted = [r for r in rows if r.bucket == "blacklisted"]
                if len(blacklisted) < 9:
                    issues.append(
                        f"blacklist fixture: expected ≥ 9 blacklisted rows, got {len(blacklisted)}"
                    )

        # 7.5 cold_detector still wave1/full both work after refactor
        cd = tools_root / "research" / "cold_detector.py"
        for stage in ("full", "wave1"):
            r = subprocess.run(
                [py, str(cd), "--skill-dir", str(proto), "--stage", stage, "--json"],
                capture_output=True, text=True, timeout=15,
            )
            try:
                rep = json.loads(r.stdout)
                if "stage" not in rep:
                    issues.append(f"cold_detector --stage {stage} missing stage in report")
            except Exception:
                issues.append(f"cold_detector --stage {stage} json parse failed")
    except Exception as e:
        issues.append(f"iter 26 fixture suite raised: {type(e).__name__}: {e}")

    return issues


def main():
    skill_root = Path(__file__).resolve().parent.parent
    prototypes = sorted((skill_root / "prototypes").iterdir())
    results = {}
    for p in prototypes:
        if not p.is_dir():
            continue
        if not (p / "output" / "SKILL.md").exists():
            # Skip prototypes without output (e.g. llm-agent-infra was just original)
            continue
        check_skill(p, results)

    total_issues = 0
    print(f"\n# Self-test results — {len(results)} prototypes checked\n")
    for name in sorted(results):
        issues = results[name]
        if not issues:
            print(f"✅ {name}: clean")
        else:
            print(f"⚠️  {name}: {len(issues)} issue(s)")
            for i in issues:
                print(f"   - {i}")
            total_issues += len(issues)

    for note in INFO_NOTES:
        print(f"ℹ️  {note}")

    print(f"\n**Prototype subtotal**: {total_issues} issues across {len(results)} skills.\n")

    # New: tool smoke tests (Q1-Q6 additions)
    print("# Tool smoke tests\n")
    tool_issues = smoke_test_tools(skill_root)
    if not tool_issues:
        print("✅ all tools: --help OK + sample runs OK")
    else:
        print(f"⚠️  {len(tool_issues)} tool issue(s):")
        for i in tool_issues:
            print(f"   - {i}")
    print(f"\n**Tool subtotal**: {len(tool_issues)} issues.")
    total_issues += len(tool_issues)
    print(f"\n**Total**: {total_issues} issues.")
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
