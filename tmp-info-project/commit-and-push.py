#!/usr/bin/env python3
"""Master script: Regra nº1 — commit & push all changed subrepos from .gitmodules.

Run this from the OntoBDC super-project root.
- Stage: status sweep -> commit+push per dirty subrepo -> commit (NO PUSH) super-project.

All events written to ./commit-and-push.log at the super-project root so we can
read them with the Read tool (the sandbox terminal suppresses stdout/stderr for
RunCommand shell calls — Write/Read tools on real project files are confirmed
write-through to disk on the host).

Conforms to:
  /Users/eliasmpjunior/.trae/user_rules/rule-1783377860040.md
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import tempfile

SUPER_ROOT = Path(
    "/Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC"
)
GITMODULES = SUPER_ROOT / ".gitmodules"
LOGFILE = SUPER_ROOT / "commit-and-push.log"
RUNTIME_MARKER = SUPER_ROOT / ".commit-runtime-marker.yaml"

# Ensure log+marker exist on disk before any run so host Read tool can locate them.
open(str(LOGFILE), "a", encoding="utf-8").close()
open(str(RUNTIME_MARKER), "a", encoding="utf-8").close()


def log(msg: str) -> None:
    with open(LOGFILE, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def git(cwd: Path, args: List[str]) -> Tuple[int, str, str]:
    res = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    return res.returncode, res.stdout, res.stderr


def parse_gitmodules(path: Path) -> List[str]:
    paths: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            m = re.match(r"\s*path\s*=\s*(.+?)\s*$", raw)
            if m:
                paths.append(m.group(1))
    return paths


def is_dirty(cwd: Path) -> bool:
    rc, out, _ = git(cwd, ["status", "--porcelain"])
    return rc == 0 and bool(out.strip())


def diff_stat(cwd: Path, staged: bool = False) -> str:
    args = ["diff", "--cached", "--stat"] if staged else ["diff", "--stat"]
    rc, out, _ = git(cwd, args)
    if rc != 0 or not out.strip():
        rc2, short, _ = git(cwd, ["status", "--short"])
        if rc2 == 0 and short.strip():
            return short
        return "(no diff)"
    return out


def count_changed_stats(stat_str: str) -> Tuple[int, int]:
    lines = [l for l in stat_str.splitlines() if l.strip()]
    if not lines:
        return 0, 0
    last = lines[-1]
    fm = re.search(r"(\d+) files? changed", last)
    files = int(fm.group(1)) if fm else 0
    im = re.search(r"(\d+) insertions?\(\+\)", last)
    dm = re.search(r"(\d+) deletions?\(-\)", last)
    churn = (int(im.group(1)) if im else 0) + (int(dm.group(1)) if dm else 0)
    return files, churn


def classify_scope(files_changed: List[str]) -> str:
    folders = set()
    for p in files_changed:
        parts = Path(p).parts
        if parts:
            folders.add(parts[0])
    if not folders:
        return "misc"
    ordered: List[str] = []
    for priority in [
        "src",
        "ontobdc",
        "cli",
        "view",
        "storage",
        "context",
        "shared",
        "develop",
        "docs",
    ]:
        if priority in folders:
            ordered.append(priority)
            folders.discard(priority)
    ordered.extend(sorted(folders))
    return ",".join(ordered[:3])


def summarize_changes(cwd: Path) -> str:
    rc, out, _ = git(cwd, ["diff", "--cached", "--name-only"])
    if rc != 0 or not out.strip():
        return "(no changed files staged)"
    files = [l.strip() for l in out.splitlines() if l.strip()]
    groups: Dict[str, List[str]] = {}
    for f in files:
        parts = Path(f).parts
        key = parts[0] if parts else "(root)"
        groups.setdefault(key, []).append(f)
    lines: List[str] = []
    for key in sorted(groups.keys()):
        grp = groups[key]
        if len(grp) == 1:
            lines.append(f"- {grp[0]}")
        else:
            names = ", ".join(os.path.basename(g) for g in grp[:5])
            tail = "…" if len(grp) > 5 else ""
            lines.append(f"- {key}/ ({len(grp)} files: {names}{tail})")
    return "\n".join(lines)


def build_subrepo_message(subrepo_name: str, cwd: Path) -> str:
    stat = diff_stat(cwd, staged=True)
    files, churn = count_changed_stats(stat)
    rc, names_out, _ = git(cwd, ["diff", "--cached", "--name-only"])
    changed = [l.strip() for l in names_out.splitlines() if l.strip()] if rc == 0 else []
    scope = classify_scope(changed)

    has_py = any(p.endswith(".py") for p in changed)
    has_docs_only = bool(changed) and all(
        p.startswith("docs/") or p.lower().endswith((".md", ".rst", ".txt"))
        for p in changed
    )
    has_ci = (
        bool(changed)
        and any(".github" in p or "ci/" in p or p.endswith((".yml", ".yaml")) for p in changed)
        and not has_py
    )

    if has_docs_only:
        typ = "docs"
    elif has_ci:
        typ = "chore(ci)"
    elif has_py:
            rc2, summary, _ = git(cwd, ["diff", "--cached", "--summary"])
            any_new = rc2 == 0 and " create mode " in summary
            typ = "feat" if any_new else "fix"
    else:
        typ = "chore"

    scope_str = f"({scope})" if not typ.endswith(")") else ""
    header = (
        f"{typ}{scope_str}: sync changes in {subrepo_name} "
        f"({files} files, {churn} churn)"
    )
    changes_summary = summarize_changes(cwd)
    body = (
        header + "\n\n"
        f"Changed files summary for subrepo `{subrepo_name}`:\n"
        f"{changes_summary}\n\n"
        "`git diff --cached --stat` output:\n```\n"
        f"{stat.rstrip()}\n```\n"
    )
    return body


def build_superproject_message(super_root: Path) -> str:
    stat = diff_stat(super_root, staged=True)
    files, churn = count_changed_stats(stat)
    rc, names_out, _ = git(super_root, ["diff", "--cached", "--name-only"])
    changed = [l.strip() for l in names_out.splitlines() if l.strip()] if rc == 0 else []
    rc2, raw, _ = git(super_root, ["diff", "--cached", "--raw"])
    updated_subs: List[str] = []
    if rc2 == 0 and raw.strip():
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].split()[-1] == "M":
                updated_subs.append(parts[-1])
    changes_summary = summarize_changes(super_root)
    if updated_subs:
        scope = "submodules"
        typ = "chore"
        header = f"{typ}({scope}): bump submodule pointers ({len(updated_subs)} subrepos)"
    else:
        scope = classify_scope(changed) or "root"
        typ = "chore"
        header = f"{typ}({scope}): superproject root updates ({files} files, {churn} churn)"
    body = header + "\n\n"
    if updated_subs:
        body += "Updated submodule pointers:\n"
        for s in updated_subs:
            body += f"- {s}\n"
        body += "\n"
    if changes_summary.strip() and changes_summary != "(no changed files staged)":
        body += "Other changed files in superproject root:\n" + changes_summary + "\n\n"
    body += (
        "`git diff --cached --stat` output:\n```\n"
        f"{stat.rstrip()}\n```\n"
    )
    return body


def main() -> int:
    # Update runtime marker first thing so host Read tool can detect the run happened.
    stamp = datetime.now().isoformat()
    with open(RUNTIME_MARKER, "w", encoding="utf-8") as fh:
        fh.write("# Runtime marker updated by commit-and-push.py at launch.\n")
        fh.write(f"started-at: {stamp}\n")
        fh.write("status: running\n")
    with open(LOGFILE, "w", encoding="utf-8") as fh:
        fh.write(
            f"=== commit-and-push run started at {stamp} ===\n"
        )
    log(f"pid={os.getpid()}")
    if not GITMODULES.is_file():
        log(f"FATAL: .gitmodules not found at {GITMODULES}")
        return 1
    subrepo_paths = parse_gitmodules(GITMODULES)
    log(f"Parsed {len(subrepo_paths)} subrepo paths from .gitmodules: {subrepo_paths!r}")

    for rel in subrepo_paths:
        cwd = SUPER_ROOT / rel
        if not cwd.is_dir():
            log(f"[{rel}] SKIP: directory missing at {cwd}")
            continue
        dirty = is_dirty(cwd)
        log(f"[{rel}] dirty={dirty}")
        if not dirty:
            continue
        # add -A
        rc, _, err = git(cwd, ["add", "-A"])
        log(f"[{rel}] git add -A rc={rc}")
        if rc != 0 and err.strip():
            log(f"  STDERR: {err.rstrip()}")
        rc2, staged, _ = git(cwd, ["diff", "--cached", "--name-only"])
        if rc2 != 0 or not staged.strip():
            log(f"[{rel}] nothing staged — skip commit/push")
            continue
        msg = build_subrepo_message(rel, cwd)
        tmp_suffix = rel.replace("/", "__")
        msg_path = Path(tempfile.mktemp(prefix=f"commit-msg-{tmp_suffix}-", suffix=".txt"))
        with open(msg_path, "w", encoding="utf-8") as fh:
            fh.write(msg)
        rc3, out3, err3 = git(cwd, ["commit", "-F", str(msg_path)])
        log(f"[{rel}] git commit rc={rc3}")
        if out3.strip():
            log(f"  STDOUT:\n{out3.rstrip()}")
        if err3.strip():
            log(f"  STDERR:\n{err3.rstrip()}")
        if rc3 != 0:
            log(f"  WARNING: commit failed; skip push")
            continue
        rc4, out4, err4 = git(cwd, ["push"])
        log(f"[{rel}] git push rc={rc4}")
        if out4.strip():
            log(f"  STDOUT:\n{out4.rstrip()}")
        if err4.strip():
            log(f"  STDERR:\n{err4.rstrip()}")

    log("---")
    log("Processing super-project root (commit ONLY, NO push per Regra nº1)")
    dirty_root = is_dirty(SUPER_ROOT)
    log(f"[SUPER:{SUPER_ROOT.name}] dirty={dirty_root}")
    if dirty_root:
        rc, _, err = git(SUPER_ROOT, ["add", "-A"])
        log(f"[SUPER] git add -A rc={rc}")
        if err.strip():
            log(f"  STDERR: {err.rstrip()}")
        rc2, staged, _ = git(SUPER_ROOT, ["diff", "--cached", "--name-only"])
        if rc2 == 0 and staged.strip():
            msg = build_superproject_message(SUPER_ROOT)
            msg_path = Path(tempfile.mktemp(prefix="commit-msg-super-", suffix=".txt"))
            with open(msg_path, "w", encoding="utf-8") as fh:
                fh.write(msg)
            rc3, out3, err3 = git(SUPER_ROOT, ["commit", "-F", str(msg_path)])
            log(f"[SUPER] git commit rc={rc3}")
            if out3.strip():
                log(f"  STDOUT:\n{out3.rstrip()}")
            if err3.strip():
                log(f"  STDERR:\n{err3.rstrip()}")
            log("[SUPER] push SKIPPED — Regra nº1: superproject SEM push")
        else:
            log("[SUPER] nothing staged — skip commit")
    else:
        log("[SUPER] clean — nothing to commit")
    log("")
    log("=== DONE ===")
    stamp_done = datetime.now().isoformat()
    with open(RUNTIME_MARKER, "a", encoding="utf-8") as fh:
        fh.write(f"finished-at: {stamp_done}\n")
        fh.write("status: done\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
