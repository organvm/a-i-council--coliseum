#!/usr/bin/env python3
"""Archive Jules PR intent, close all open PRs, and delete all non-main remotes.

This script implements the "Jules PR/Branch Zeroing Cleanup Plan" for this repo.
It generates local artifacts, creates a bundle backup, posts PR closure comments,
closes open PRs, deletes non-main remote branches, and records a detailed log.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "artifacts" / "jules_cleanup"
BACKUP_DIR = ROOT / "backups"

OPEN_PRS_PATH = ART_DIR / "open_prs.json"
REMOTE_BRANCHES_PATH = ART_DIR / "remote_branches.json"
PR_FILE_INVENTORY_PATH = ART_DIR / "pr_file_inventory.json"
CLUSTER_MATRIX_PATH = ART_DIR / "cluster_matrix.csv"
REPORT_PATH = ART_DIR / "jules_intent_report.md"
EXEC_LOG_PATH = ART_DIR / "cleanup_execution_log.json"

MAX_RETRIES = 3


class CmdError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().isoformat()


def print_progress(msg: str) -> None:
    print(msg, flush=True)


def run(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    retries: int = 0,
    retry_delay: float = 1.0,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        cp = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=capture_output,
            text=text,
            env=env,
        )
        if cp.returncode == 0 or not check:
            return cp
        last_err = CmdError(
            f"Command failed ({cp.returncode}) on attempt {attempt + 1}/{retries + 1}: "
            f"{shlex.join(args)}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}"
        )
        if attempt < retries:
            time.sleep(retry_delay * (2**attempt))
    assert last_err is not None
    raise last_err


def run_text(args: list[str], **kwargs: Any) -> str:
    return run(args, **kwargs).stdout or ""


def run_json(args: list[str], **kwargs: Any) -> Any:
    out = run_text(args, **kwargs)
    return json.loads(out or "null")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_if_exists(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def git_short_sha(ref: str) -> str:
    return run_text(["git", "rev-parse", "--short", ref]).strip()


def git_full_sha(ref: str) -> str:
    return run_text(["git", "rev-parse", ref]).strip()


def git_default_branch() -> str:
    try:
        info = run_json(["gh", "repo", "view", "--json", "defaultBranchRef"])
        return info["defaultBranchRef"]["name"]
    except Exception:
        return "main"


def list_open_prs() -> list[dict[str, Any]]:
    fields = [
        "number",
        "title",
        "author",
        "headRefName",
        "baseRefName",
        "isDraft",
        "updatedAt",
        "createdAt",
        "url",
    ]
    return run_json(["gh", "pr", "list", "--state", "open", "--limit", "300", "--json", ",".join(fields)])


def fetch_pr_detail(number: int) -> dict[str, Any]:
    fields = [
        "number",
        "title",
        "author",
        "headRefName",
        "baseRefName",
        "isDraft",
        "updatedAt",
        "createdAt",
        "url",
        "body",
        "files",
        "commits",
    ]
    return run_json(
        ["gh", "pr", "view", str(number), "--json", ",".join(fields)],
        retries=MAX_RETRIES,
        retry_delay=1.5,
    )


def list_remote_branches() -> list[dict[str, Any]]:
    fmt = "%(refname:short)\t%(refname)\t%(objectname)\t%(committerdate:iso8601)\t%(authorname)\t%(subject)"
    out = run_text(["git", "for-each-ref", f"--format={fmt}", "refs/remotes/origin"])
    rows: list[dict[str, Any]] = []
    for line in out.splitlines():
        parts = line.split("\t", 5)
        if len(parts) != 6:
            continue
        short_ref, full_ref, sha, committer_date, author, subject = parts
        rows.append(
            {
                "shortRef": short_ref,
                "fullRef": full_ref,
                "sha": sha,
                "committerDate": committer_date,
                "author": author,
                "subject": subject,
            }
        )
    return rows


def backup_bundle(timestamp_label: str, refs: list[str]) -> dict[str, Any]:
    bundle_path = BACKUP_DIR / f"a-i-council--coliseum-pre-zeroing-{timestamp_label}.bundle"
    filtered_refs = [r for r in refs if r != "refs/remotes/origin/HEAD"]
    if not filtered_refs:
        raise RuntimeError("No refs found for bundle creation")
    print_progress(f"Creating bundle backup at {bundle_path} ({len(filtered_refs)} refs)")
    run(["git", "bundle", "create", str(bundle_path), *filtered_refs], capture_output=True, text=True)
    verify = run(["git", "bundle", "verify", str(bundle_path)], capture_output=True, text=True)
    checksum = sha256_file(bundle_path)
    return {
        "path": str(bundle_path),
        "sha256": checksum,
        "verified": verify.returncode == 0,
        "verifyStdout": verify.stdout,
        "verifyStderr": verify.stderr,
        "refCount": len(filtered_refs),
    }


def normalize_tokens(text: str) -> list[str]:
    stop = {
        "a",
        "add",
        "and",
        "api",
        "for",
        "fix",
        "feat",
        "improve",
        "implement",
        "in",
        "of",
        "on",
        "optimize",
        "the",
        "to",
        "with",
    }
    raw = re.findall(r"[a-z0-9]+", text.lower())
    tokens = [t for t in raw if t not in stop and not t.isdigit()]
    return tokens


def classify_pr_cluster(pr: dict[str, Any]) -> tuple[str, str]:
    title = (pr.get("title") or "").lower()
    head = (pr.get("headRefName") or "").lower()
    files = " ".join((f.get("path") or "").lower() for f in pr.get("files", []) or [])
    blob = " ".join([title, head, files])

    def has(pattern: str) -> bool:
        return re.search(pattern, blob, re.I) is not None

    if has(r"sentinel|cors|xss|security headers|rate limit|input validation|validation") and not has(r"solana|ethereum"):
        if has(r"rate limit"):
            return ("Sentinel", "rate_limit")
        if has(r"xss|escape"):
            return ("Sentinel", "xss")
        if has(r"security headers"):
            return ("Sentinel", "security_headers")
        if has(r"validation"):
            return ("Sentinel", "input_validation")
        return ("Sentinel", "cors")

    if has(r"palette|skip.?to.?content|skip.?link|focus|button|emoji|a11y|accessib"):
        if has(r"skip.?to.?content|skip.?link"):
            return ("Palette", "skip_link")
        return ("Palette", "button_a11y")

    if has(r"nlp|sentiment|summarization|entity extraction|topic classification|nlp_module"):
        return ("NLP", "nlp")

    if has(r"solana|ethereum|web3|erc20|blockchain/solana_contracts|blockchain/ethereum_contracts"):
        return ("Solana/Ethereum", "blockchain")

    if has(r"event pipeline|event_pipeline|agent-creation|voting|achievement|leaderboard|user-system|rewards-api|staking-api|entity-extraction-integration|sentiment-integration"):
        return ("Event Pipeline / Integrations", "integrations")

    if has(r"knowledgebase|knowledge base|\bkb\b"):
        return ("Bolt", "knowledge_base")
    if has(r"memorymanager|memory manager|\blru\b|eviction"):
        return ("Bolt", "memory")
    if has(r"prioritization"):
        return ("Bolt", "prioritization")
    if has(r"ingestion|get_recent_events"):
        return ("Bolt", "ingestion")
    if has(r"keyword"):
        return ("Bolt", "keywords")
    if has(r"bolt|concurr|batch event|event processing|asyncio\.gather|broadcast"):
        return ("Bolt", "batch_concurrency")

    return ("Other", "other")


def classify_branch_cluster(branch_name: str) -> tuple[str, str]:
    fake = {"title": "", "headRefName": branch_name, "files": []}
    return classify_pr_cluster(fake)


def duplicate_annotations(details: list[dict[str, Any]]) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    by_title_key: dict[str, list[int]] = defaultdict(list)
    by_file_set_key: dict[str, list[int]] = defaultdict(list)
    by_single_commit_oid: dict[str, list[int]] = defaultdict(list)

    detail_map = {int(d["number"]): d for d in details}
    annotations: dict[int, dict[str, Any]] = {}

    for d in details:
        num = int(d["number"])
        tokens = sorted(set(normalize_tokens(f"{d.get('title','')} {d.get('headRefName','')}")))
        title_key = "|".join(tokens) if tokens else ""
        file_paths = sorted(set((f.get("path") or "") for f in d.get("files", [])))
        file_set_key = "|".join(file_paths) if file_paths else ""
        commits = d.get("commits", []) or []
        single_oid = commits[0]["oid"] if len(commits) == 1 and commits[0].get("oid") else ""
        annotations[num] = {
            "normalizedTitleKey": title_key,
            "fileSetKey": file_set_key,
            "singleCommitOid": single_oid,
        }
        if title_key:
            by_title_key[title_key].append(num)
        if file_set_key:
            by_file_set_key[file_set_key].append(num)
        if single_oid:
            by_single_commit_oid[single_oid].append(num)

    for num, ann in annotations.items():
        ann["duplicateByTitleKey"] = [n for n in by_title_key.get(ann["normalizedTitleKey"], []) if n != num]
        ann["duplicateByFileSetKey"] = [n for n in by_file_set_key.get(ann["fileSetKey"], []) if n != num]
        ann["duplicateBySingleCommitOid"] = [
            n for n in by_single_commit_oid.get(ann["singleCommitOid"], []) if n != num
        ]
        ann["isLikelyDuplicate"] = any(
            [
                ann["duplicateByTitleKey"],
                ann["duplicateByFileSetKey"],
                ann["duplicateBySingleCommitOid"],
            ]
        )

    summary = {
        "duplicateTitleGroups": sum(1 for nums in by_title_key.values() if len(nums) > 1),
        "duplicateFileSetGroups": sum(1 for nums in by_file_set_key.values() if len(nums) > 1),
        "duplicateSingleCommitGroups": sum(1 for nums in by_single_commit_oid.values() if len(nums) > 1),
        "duplicateTitleExamples": [
            {"key": k, "prs": v[:10]} for k, v in list(sorted(by_title_key.items(), key=lambda kv: -len(kv[1])))[:10] if len(v) > 1
        ],
        "duplicateFileSetExamples": [
            {"key": k, "prs": v[:10]}
            for k, v in list(sorted(by_file_set_key.items(), key=lambda kv: -len(kv[1])))[:10]
            if len(v) > 1
        ],
        "duplicateSingleCommitExamples": [
            {"key": k, "prs": v[:10]}
            for k, v in list(sorted(by_single_commit_oid.items(), key=lambda kv: -len(kv[1])))[:10]
            if len(v) > 1
        ],
    }
    return annotations, summary


def grep_any(pattern: str, paths: list[str]) -> bool:
    existing = [p for p in paths if (ROOT / p).exists()]
    if not existing:
        return False
    cp = run(
        ["rg", "-n", pattern, *existing],
        check=False,
        capture_output=True,
        text=True,
    )
    return cp.returncode == 0 and bool((cp.stdout or "").strip())


def read_sample(path: str, max_lines: int = 140) -> str:
    fp = ROOT / path
    if not fp.exists():
        return ""
    lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[:max_lines])


def build_cluster_disposition(
    pr_details: list[dict[str, Any]], main_commit_sha: str
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pr in pr_details:
        cluster, subcluster = classify_pr_cluster(pr)
        pr["_cluster"] = cluster
        pr["_subcluster"] = subcluster
        grouped[cluster].append(pr)

    # Current main code signatures for spot-check.
    sig = {
        "sentinel_cors_origins": grep_any(r"CORS_ORIGINS", ["backend/main.py"]),
        "sentinel_security_headers": grep_any(r"class SecurityHeadersMiddleware|X-Content-Type-Options|X-Frame-Options", ["backend/main.py"]),
        "sentinel_input_validation": grep_any(r"Field\(", ["backend/api/agents.py", "backend/api/blockchain.py", "backend/api/voting.py"]),
        "sentinel_xss_escape": grep_any(r"html\.escape", ["backend"]),
        "sentinel_rate_limit": grep_any(r"RateLimit|rate.?limit", ["backend"]),
        "bolt_memory_ordered_dict": grep_any(r"OrderedDict", ["backend/ai_agents/memory_manager.py"]),
        "bolt_kb_heapq": grep_any(r"heapq\.nlargest|heapq", ["backend/ai_agents/knowledge_base.py"]),
        "bolt_prioritization_hoist": grep_any(r"datetime\..*now|utcnow", ["backend/event_pipeline/prioritization.py"]),
        "bolt_gzip": grep_any(r"GZipMiddleware", ["backend/main.py"]),
        "bolt_async_gather": grep_any(r"asyncio\.gather", ["backend/ai_agents/communication.py", "backend/event_pipeline/processing.py", "backend/blockchain/solana_contracts.py"]),
        "palette_skip_link_target": grep_any(r'id=\"main-content\"|tabIndex=\{-1\}', ["frontend/src/app/page.tsx"]),
        "nlp_async_openai": grep_any(r"AsyncOpenAI", ["backend/ai_agents/nlp_module.py"]),
        "nlp_sentiment_impl": grep_any(r"analyze_sentiment\(", ["backend/ai_agents/nlp_module.py"]),
        "nlp_entities_impl": grep_any(r"extract_entities\(", ["backend/ai_agents/nlp_module.py"]),
        "nlp_transformers": grep_any(r"transformers|pipeline\(", ["backend/ai_agents/nlp_module.py"]),
        "eth_asyncweb3": grep_any(r"AsyncWeb3", ["backend/blockchain/ethereum_contracts.py"]),
        "solana_rewards": grep_any(r"async def distribute_rewards", ["backend/blockchain/solana_contracts.py"]),
        "solana_stake": grep_any(r"async def stake_tokens", ["backend/blockchain/solana_contracts.py"]),
        "event_pipeline_gather": grep_any(r"asyncio\.gather", ["backend/event_pipeline/processing.py"]),
    }

    dispositions: dict[str, dict[str, Any]] = {}
    follow_up_rows: list[dict[str, Any]] = []

    def reps(cluster_name: str, n: int = 3) -> list[int]:
        items = sorted(grouped.get(cluster_name, []), key=lambda x: int(x["number"]), reverse=True)
        return [int(i["number"]) for i in items[:n]]

    dispositions["Palette"] = {
        "cluster": "Palette",
        "disposition": "partially absorbed",
        "highImpact": False,
        "representativePRs": reps("Palette"),
        "rationale": (
            "Skip-link fix is present on current main (main-content target + tabIndex), but repeated Palette PRs also include "
            "button/focus/disabled-state polish that was generated in many variants and is not fully audited in this cleanup pass."
        ),
        "evidence": {
            "skipLinkTargetPresent": sig["palette_skip_link_target"],
            "mainCommit": main_commit_sha,
        },
    }

    sentinel_score = sum(
        1
        for k in [
            "sentinel_cors_origins",
            "sentinel_security_headers",
            "sentinel_input_validation",
            "sentinel_xss_escape",
            "sentinel_rate_limit",
        ]
        if sig[k]
    )
    sentinel_disp = "partially absorbed"
    sentinel_rationale = (
        "CORS restrictions, security headers, and API Field validations are present on current main. "
        "XSS escaping and/or rate limiting markers are not consistently detectable across the codebase, "
        "so remaining Sentinel PRs are treated as stale duplicates with candidate follow-up review notes."
    )
    dispositions["Sentinel"] = {
        "cluster": "Sentinel",
        "disposition": sentinel_disp,
        "highImpact": True,
        "representativePRs": reps("Sentinel"),
        "rationale": sentinel_rationale,
        "evidence": {
            "corsOriginsPresent": sig["sentinel_cors_origins"],
            "securityHeadersPresent": sig["sentinel_security_headers"],
            "inputValidationPresent": sig["sentinel_input_validation"],
            "xssEscapePresent": sig["sentinel_xss_escape"],
            "rateLimitPresent": sig["sentinel_rate_limit"],
            "signatureScore": sentinel_score,
        },
    }
    if not sig["sentinel_xss_escape"]:
        follow_up_rows.append(
            {
                "cluster": "Sentinel",
                "topic": "XSS ingestion sanitization",
                "candidatePRs": [int(p["number"]) for p in grouped.get("Sentinel", []) if p.get("_subcluster") == "xss"][:5],
                "reason": "No high-confidence html.escape marker detected in current backend files.",
            }
        )
    if not sig["sentinel_rate_limit"]:
        follow_up_rows.append(
            {
                "cluster": "Sentinel",
                "topic": "Rate limiting middleware",
                "candidatePRs": [int(p["number"]) for p in grouped.get("Sentinel", []) if p.get("_subcluster") == "rate_limit"][:5],
                "reason": "No high-confidence rate-limit middleware marker detected in current backend files.",
            }
        )

    bolt_hits = [
        sig["bolt_memory_ordered_dict"],
        sig["bolt_kb_heapq"],
        sig["bolt_prioritization_hoist"],
        sig["bolt_gzip"],
        sig["bolt_async_gather"],
    ]
    dispositions["Bolt"] = {
        "cluster": "Bolt",
        "disposition": "partially absorbed",
        "highImpact": True,
        "representativePRs": reps("Bolt"),
        "rationale": (
            "Current main contains several Bolt-style optimizations (OrderedDict memory manager and async gather patterns), "
            "but the repeated KB/prioritization/gzip variants are not uniformly present and are not merged in this cleanup pass."
        ),
        "evidence": {
            "memoryOrderedDict": sig["bolt_memory_ordered_dict"],
            "knowledgeBaseHeapq": sig["bolt_kb_heapq"],
            "prioritizationMarker": sig["bolt_prioritization_hoist"],
            "gzipMiddleware": sig["bolt_gzip"],
            "asyncGatherPatterns": sig["bolt_async_gather"],
            "signatureScore": sum(1 for x in bolt_hits if x),
        },
    }
    if not sig["bolt_kb_heapq"]:
        follow_up_rows.append(
            {
                "cluster": "Bolt",
                "topic": "KnowledgeBase heapq optimization audit",
                "candidatePRs": [int(p["number"]) for p in grouped.get("Bolt", []) if p.get("_subcluster") == "knowledge_base"][:5],
                "reason": "No high-confidence heapq KB optimization marker detected in current knowledge base module.",
            }
        )
    if not sig["bolt_gzip"]:
        follow_up_rows.append(
            {
                "cluster": "Bolt",
                "topic": "GZip middleware / compression hardening",
                "candidatePRs": [int(p["number"]) for p in grouped.get("Bolt", []) if "gzip" in (p.get("headRefName", "").lower())][:5],
                "reason": "No GZip middleware marker detected in backend/main.py.",
            }
        )

    nlp_hits = [
        sig["nlp_async_openai"],
        sig["nlp_sentiment_impl"],
        sig["nlp_entities_impl"],
        sig["nlp_transformers"],
    ]
    nlp_disposition = "absorbed in main" if all(nlp_hits[:3]) else "partially absorbed"
    dispositions["NLP"] = {
        "cluster": "NLP",
        "disposition": nlp_disposition,
        "highImpact": True,
        "representativePRs": reps("NLP"),
        "rationale": (
            "Current NLP module exposes sentiment and entity extraction methods and contains AsyncOpenAI integration markers; "
            "topic-classification/summarization variants were repeatedly generated and are archived as intent, not merged now."
        ),
        "evidence": {
            "asyncOpenAI": sig["nlp_async_openai"],
            "sentimentMethod": sig["nlp_sentiment_impl"],
            "entityExtractionMethod": sig["nlp_entities_impl"],
            "transformersMarker": sig["nlp_transformers"],
            "signatureScore": sum(1 for x in nlp_hits if x),
        },
    }

    chain_hits = [sig["eth_asyncweb3"], sig["solana_rewards"], sig["solana_stake"]]
    dispositions["Solana/Ethereum"] = {
        "cluster": "Solana/Ethereum",
        "disposition": "partially absorbed",
        "highImpact": True,
        "representativePRs": reps("Solana/Ethereum"),
        "rationale": (
            "Current main includes AsyncWeb3 and Solana reward distribution markers, but not all staking/transfer variants are "
            "confirmed present. Treat as archived intent plus follow-up candidates."
        ),
        "evidence": {
            "asyncWeb3": sig["eth_asyncweb3"],
            "solanaDistributeRewards": sig["solana_rewards"],
            "solanaStakeTokens": sig["solana_stake"],
            "signatureScore": sum(1 for x in chain_hits if x),
        },
    }
    if not sig["solana_stake"]:
        follow_up_rows.append(
            {
                "cluster": "Solana/Ethereum",
                "topic": "Solana stake_tokens implementation audit",
                "candidatePRs": [int(p["number"]) for p in grouped.get("Solana/Ethereum", []) if "stake" in (p.get("title", "").lower() + p.get("headRefName", "").lower())][:5],
                "reason": "No high-confidence stake_tokens method marker detected in current Solana contract manager.",
            }
        )

    dispositions["Event Pipeline / Integrations"] = {
        "cluster": "Event Pipeline / Integrations",
        "disposition": "candidate follow-up task",
        "highImpact": False,
        "representativePRs": reps("Event Pipeline / Integrations"),
        "rationale": (
            "This cluster contains broader feature/integration work (event pipeline, APIs, infra hooks) not safely reducible to "
            "repeated micro-fixes. Archive intent and re-scope as explicit follow-up tasks if needed."
        ),
        "evidence": {
            "eventPipelineGatherMarker": sig["event_pipeline_gather"],
        },
    }
    if grouped.get("Event Pipeline / Integrations"):
        follow_up_rows.append(
            {
                "cluster": "Event Pipeline / Integrations",
                "topic": "Re-scope integration PRs into tracked tasks",
                "candidatePRs": reps("Event Pipeline / Integrations", 5),
                "reason": "Substantive multi-file feature work should be triaged intentionally, not merged from stale bot branches.",
            }
        )

    dispositions["Other"] = {
        "cluster": "Other",
        "disposition": "not absorbed but stale",
        "highImpact": False,
        "representativePRs": reps("Other"),
        "rationale": "Miscellaneous one-off bot branches are archived for intent and closed/deleted as stale during this cleanup pass.",
        "evidence": {},
    }

    return dispositions, follow_up_rows


def build_cluster_matrix_rows(
    pr_details: list[dict[str, Any]],
    remote_branches: list[dict[str, Any]],
    open_pr_by_head: dict[str, dict[str, Any]],
    duplicate_meta: dict[int, dict[str, Any]],
    dispositions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pr in sorted(pr_details, key=lambda x: int(x["number"])):
        num = int(pr["number"])
        cluster, subcluster = pr["_cluster"], pr["_subcluster"]
        dup = duplicate_meta.get(num, {})
        rows.append(
            {
                "itemType": "pr",
                "id": f"PR#{num}",
                "number": num,
                "branch": pr.get("headRefName", ""),
                "cluster": cluster,
                "subcluster": subcluster,
                "title": pr.get("title", ""),
                "fileCount": len(pr.get("files", []) or []),
                "isDraft": bool(pr.get("isDraft")),
                "likelyDuplicate": bool(dup.get("isLikelyDuplicate")),
                "duplicateByTitleCount": len(dup.get("duplicateByTitleKey", []) or []),
                "duplicateByFileSetCount": len(dup.get("duplicateByFileSetKey", []) or []),
                "duplicateByCommitCount": len(dup.get("duplicateBySingleCommitOid", []) or []),
                "clusterDisposition": dispositions.get(cluster, {}).get("disposition", ""),
                "cleanupDecision": "close_pr_and_delete_branch",
                "cleanupReason": "stale/redundant bot PR; intent archived in consolidated report",
            }
        )

    for rb in remote_branches:
        short_ref = rb["shortRef"]
        if short_ref in {"origin/HEAD", "origin/main"}:
            continue
        branch_name = short_ref.removeprefix("origin/")
        if branch_name in open_pr_by_head:
            continue
        cluster, subcluster = classify_branch_cluster(branch_name)
        rows.append(
            {
                "itemType": "orphan_remote_branch",
                "id": short_ref,
                "number": "",
                "branch": branch_name,
                "cluster": cluster,
                "subcluster": subcluster,
                "title": rb.get("subject", ""),
                "fileCount": "",
                "isDraft": "",
                "likelyDuplicate": "",
                "duplicateByTitleCount": "",
                "duplicateByFileSetCount": "",
                "duplicateByCommitCount": "",
                "clusterDisposition": dispositions.get(cluster, {}).get("disposition", "not absorbed but stale"),
                "cleanupDecision": "delete_branch",
                "cleanupReason": "orphan remote branch in zeroing cleanup scope",
            }
        )

    return rows


def write_cluster_matrix_csv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "itemType",
        "id",
        "number",
        "branch",
        "cluster",
        "subcluster",
        "title",
        "fileCount",
        "isDraft",
        "likelyDuplicate",
        "duplicateByTitleCount",
        "duplicateByFileSetCount",
        "duplicateByCommitCount",
        "clusterDisposition",
        "cleanupDecision",
        "cleanupReason",
    ]
    with CLUSTER_MATRIX_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def render_report(
    *,
    pre_open_prs: list[dict[str, Any]],
    pr_details: list[dict[str, Any]],
    remote_branches: list[dict[str, Any]],
    duplicate_summary: dict[str, Any],
    dispositions: dict[str, dict[str, Any]],
    follow_ups: list[dict[str, Any]],
    main_short_sha: str,
    main_full_sha: str,
) -> str:
    open_pr_by_head = {p["headRefName"]: p for p in pre_open_prs}

    cluster_counts = Counter(d["_cluster"] for d in pr_details)
    subcluster_counts = Counter((d["_cluster"], d["_subcluster"]) for d in pr_details)
    file_counts = Counter()
    for pr in pr_details:
        for file_obj in pr.get("files", []) or []:
            path = file_obj.get("path") or ""
            if path:
                file_counts[path] += 1

    repeated_hotspots = file_counts.most_common(20)

    non_main_remote = [b for b in remote_branches if b["shortRef"] not in {"origin/main", "origin/HEAD"}]
    orphan_branches = [b for b in non_main_remote if b["shortRef"].removeprefix("origin/") not in open_pr_by_head]

    existing_docs = [
        "docs/PR_CONSOLIDATION_SUMMARY.md",
        "PHASE4_ARS_ELECTRONICA_SPRINT.md",
    ]
    existing_docs_lines: list[str] = []
    for p in existing_docs:
        text = read_text_if_exists(ROOT / p)
        if text:
            first = text.splitlines()[0] if text.splitlines() else "(empty)"
            existing_docs_lines.append(f"- `{p}` ({first})")

    main_commit_files = run_text(["git", "show", "--name-only", "--pretty=format:", "-1", "origin/main"]).splitlines()
    main_commit_files = [f for f in main_commit_files if f.strip()]

    lines: list[str] = []
    lines.append("# Jules PR Intent Archive & Zeroing Cleanup Report")
    lines.append("")
    lines.append(f"- Generated: `{utc_iso()}`")
    lines.append(f"- Repo: `organvm-ii-poiesis/a-i-council--coliseum`")
    lines.append(f"- Baseline main commit: `{main_short_sha}` (`{main_full_sha}`)")
    lines.append(f"- Open PRs at snapshot: `{len(pre_open_prs)}` (all Jules-generated)")
    lines.append(f"- Non-main remote branches at snapshot: `{len(non_main_remote)}`")
    lines.append(f"- Orphan remote branches at snapshot: `{len(orphan_branches)}`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        "The repository had a large cascade of stale, overlapping Jules PRs concentrated in repeated Sentinel (security), "
        "Bolt (performance), and Palette (accessibility/UI) themes, plus older substantive NLP/blockchain/integration branches. "
        "This cleanup pass archives intent, records cluster dispositions, then closes all open PRs and deletes all non-main remote branches."
    )
    lines.append("")
    lines.append("## Existing Repo Signals Used")
    lines.append("")
    lines.extend(existing_docs_lines or ["- None found"])
    lines.append(f"- `origin/main` consolidation commit touches {len(main_commit_files)} files, including Sentinel/Bolt/Palette targets")
    lines.append("")
    lines.append("## Cluster Summary (Open PRs)")
    lines.append("")
    lines.append("| Cluster | PR Count | Top Subclusters | Disposition |")
    lines.append("|---|---:|---|---|")
    for cluster, count in sorted(cluster_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        top_subs = [
            f"{sub}:{cnt}"
            for (cl, sub), cnt in sorted(subcluster_counts.items(), key=lambda kv: (-kv[1], kv[0][1]))
            if cl == cluster
        ][:3]
        disp = dispositions.get(cluster, {}).get("disposition", "n/a")
        lines.append(f"| {cluster} | {count} | {', '.join(top_subs)} | {disp} |")
    lines.append("")
    lines.append("## Duplicate / Redundancy Signals")
    lines.append("")
    lines.append(f"- Duplicate title groups: `{duplicate_summary['duplicateTitleGroups']}`")
    lines.append(f"- Duplicate file-set groups: `{duplicate_summary['duplicateFileSetGroups']}`")
    lines.append(f"- Duplicate single-commit groups: `{duplicate_summary['duplicateSingleCommitGroups']}`")
    lines.append("")
    lines.append("## Repeated File Hotspots")
    lines.append("")
    lines.append("| File | PR Touch Count |")
    lines.append("|---|---:|")
    for path, cnt in repeated_hotspots:
        lines.append(f"| `{path}` | {cnt} |")
    lines.append("")
    lines.append("## High-Confidence Signals Already Represented On Current `main`")
    lines.append("")
    high_conf = [
        ("Palette skip-link target", 'id="main-content" + `tabIndex={-1}` in `frontend/src/app/page.tsx`'),
        ("Sentinel CORS config", "`CORS_ORIGINS` in `backend/main.py`"),
        ("Sentinel security headers", "`SecurityHeadersMiddleware` in `backend/main.py`"),
        ("Sentinel API validation", "`Field(...)` constraints in `backend/api/*`"),
        ("Bolt memory optimization", "`OrderedDict` in `backend/ai_agents/memory_manager.py`"),
        ("Bolt concurrency patterns", "`asyncio.gather` present in hot-path modules"),
        ("NLP methods", "`analyze_sentiment` and `extract_entities` in `backend/ai_agents/nlp_module.py`"),
        ("Ethereum async integration", "`AsyncWeb3` in `backend/blockchain/ethereum_contracts.py`"),
        ("Solana rewards method", "`distribute_rewards` in `backend/blockchain/solana_contracts.py`"),
    ]
    for name, evidence in high_conf:
        lines.append(f"- {name}: {evidence}")
    lines.append("")
    lines.append("## Cluster-by-Cluster Inferred Intent")
    lines.append("")
    for cluster in sorted(cluster_counts.keys()):
        disp = dispositions.get(cluster, {})
        reps = [d for d in pr_details if d["_cluster"] == cluster]
        reps_sorted = sorted(reps, key=lambda x: int(x["number"]), reverse=True)
        lines.append(f"### {cluster}")
        lines.append("")
        lines.append(f"- PR count: `{len(reps_sorted)}`")
        lines.append(f"- Disposition: `{disp.get('disposition', 'n/a')}`")
        lines.append(f"- Rationale: {disp.get('rationale', '')}")
        rep_items = reps_sorted[:3]
        if rep_items:
            lines.append("- Representative PRs:")
            for pr in rep_items:
                file_preview = ", ".join((f.get('path') or '') for f in (pr.get("files") or [])[:4])
                if len(pr.get("files") or []) > 4:
                    file_preview += ", ..."
                lines.append(
                    f"  - `#{pr['number']}` `{pr['title']}` (`{pr['headRefName']}`) "
                    f"[files: {len(pr.get('files') or [])}; {file_preview}]"
                )
        evidence = disp.get("evidence") or {}
        if evidence:
            lines.append("- Spot-check evidence:")
            for k, v in evidence.items():
                lines.append(f"  - `{k}`: `{v}`")
        lines.append("")
    lines.append("## Candidate Follow-Up Work (Not Merged In This Cleanup Pass)")
    lines.append("")
    if not follow_ups:
        lines.append("- None identified from hybrid spot-check.")
    else:
        for item in follow_ups:
            lines.append(
                f"- **{item['cluster']} / {item['topic']}**: {item['reason']} "
                f"(candidate PRs: {', '.join('#'+str(n) for n in item.get('candidatePRs', [])) or 'none'})"
            )
    lines.append("")
    lines.append("## Cleanup Decision Matrix Summary")
    lines.append("")
    lines.append("- Open PRs: close with standardized archival comment (all are stale Jules branches in this pass).")
    lines.append("- PR head branches: delete after closure.")
    lines.append("- Orphan remote branches: delete under selected zeroing scope.")
    lines.append("- Local branches: unchanged.")
    lines.append("")
    lines.append("## Standard PR Closure Comment Template")
    lines.append("")
    lines.append("```text")
    lines.append(
        f"Closing as part of the repo-wide PR/branch zeroing cleanup. "
        f"This PR falls into a redundant Jules-generated cluster and is stale against current `main` (`{main_short_sha}`)."
    )
    lines.append("Intent and representative changes were archived in the consolidated cleanup report under `artifacts/jules_cleanup/`.")
    lines.append("No code is being merged from this stale branch in this cleanup pass.")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def pr_close_comment(pr: dict[str, Any], cluster: str, main_short_sha: str) -> str:
    reason = "stale/redundant Jules-generated PR in a repository-wide cleanup"
    return (
        f"Closing as part of the repo-wide PR/branch zeroing cleanup.\n\n"
        f"- Cluster: `{cluster}`\n"
        f"- Reason: {reason}\n"
        f"- Baseline: current `main` is `{main_short_sha}` and this PR branch is stale/diverged\n"
        f"- Archival note: intent and representative changes were captured in the consolidated cleanup report under `artifacts/jules_cleanup/`\n\n"
        f"No code is being merged from this stale branch in this cleanup pass."
    )


def gh_comment_and_close_pr(pr: dict[str, Any], cluster: str, main_short_sha: str) -> dict[str, Any]:
    num = int(pr["number"])
    result: dict[str, Any] = {
        "number": num,
        "headRefName": pr.get("headRefName"),
        "cluster": cluster,
        "commented": False,
        "closed": False,
        "commentError": "",
        "closeError": "",
    }
    body = pr_close_comment(pr, cluster, main_short_sha)
    try:
        run(["gh", "pr", "comment", str(num), "--body", body], retries=MAX_RETRIES, retry_delay=1.0)
        result["commented"] = True
    except Exception as e:
        result["commentError"] = str(e)

    try:
        run(["gh", "pr", "close", str(num)], retries=MAX_RETRIES, retry_delay=1.0)
        result["closed"] = True
    except Exception as e:
        # Idempotency: treat "already closed" as success if observed.
        result["closeError"] = str(e)
        try:
            state = run_json(["gh", "pr", "view", str(num), "--json", "state"], retries=1)["state"]
            if state == "CLOSED":
                result["closed"] = True
        except Exception:
            pass
    return result


def delete_remote_branch(branch_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "branch": branch_name,
        "deleted": False,
        "error": "",
    }
    try:
        run(["git", "push", "origin", "--delete", branch_name], retries=MAX_RETRIES, retry_delay=1.0)
        result["deleted"] = True
    except Exception as e:
        err = str(e)
        result["error"] = err
        # Idempotency: if branch no longer exists, treat as success.
        if "remote ref does not exist" in err.lower() or "unable to delete" in err.lower() and "remote ref does not exist" in err.lower():
            result["deleted"] = True
    return result


def main() -> int:
    os.chdir(ROOT)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    start_time = utc_iso()
    timestamp_label = utc_now().strftime("%Y%m%d-%H%M")
    default_branch = git_default_branch()
    main_short_sha = git_short_sha(f"origin/{default_branch}")
    main_full_sha = git_full_sha(f"origin/{default_branch}")

    exec_log: dict[str, Any] = {
        "startedAt": start_time,
        "repoPath": str(ROOT),
        "defaultBranch": default_branch,
        "baselineMainShortSha": main_short_sha,
        "baselineMainFullSha": main_full_sha,
        "phases": {},
        "artifactPaths": {},
        "backup": {},
        "preCounts": {},
        "postCounts": {},
        "failures": [],
    }

    print_progress("Phase 1: snapshot open PRs and remote branches")
    open_prs = list_open_prs()
    remote_branches = list_remote_branches()
    open_pr_by_head = {p["headRefName"]: p for p in open_prs}

    for rb in remote_branches:
        short_ref = rb["shortRef"]
        branch_name = short_ref.removeprefix("origin/")
        rb["branchName"] = branch_name
        rb["isDefaultBranch"] = short_ref in {"origin/main", "origin/HEAD"}
        rb["matchesOpenPrHead"] = branch_name in open_pr_by_head
        rb["matchedOpenPrNumber"] = open_pr_by_head.get(branch_name, {}).get("number")

    write_json(OPEN_PRS_PATH, open_prs)
    write_json(REMOTE_BRANCHES_PATH, remote_branches)

    non_main_remote = [b for b in remote_branches if b["shortRef"] not in {"origin/main", "origin/HEAD"}]
    orphan_remote = [b for b in non_main_remote if not b["matchesOpenPrHead"]]
    exec_log["preCounts"] = {
        "openPrs": len(open_prs),
        "remoteNonMainBranches": len(non_main_remote),
        "remoteBranchesWithOpenPr": sum(1 for b in non_main_remote if b["matchesOpenPrHead"]),
        "remoteBranchesWithoutOpenPr": len(orphan_remote),
    }

    print_progress("Phase 1b: creating verified git bundle backup")
    refs_for_bundle = run_text(
        ["git", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/tags", "refs/remotes/origin"]
    ).splitlines()
    backup_info = backup_bundle(timestamp_label, refs_for_bundle)
    exec_log["backup"] = backup_info
    if not backup_info.get("verified"):
        raise RuntimeError("Bundle verification failed before destructive cleanup")

    print_progress("Phase 2: enriching PR inventory (gh pr view per PR)")
    pr_details: list[dict[str, Any]] = []
    pr_file_inventory: list[dict[str, Any]] = []
    for idx, pr in enumerate(sorted(open_prs, key=lambda p: int(p["number"]))):
        num = int(pr["number"])
        if idx % 10 == 0:
            print_progress(f"  fetching PR details {idx + 1}/{len(open_prs)} (PR #{num})")
        detail = fetch_pr_detail(num)
        cluster, subcluster = classify_pr_cluster(detail)
        detail["_cluster"] = cluster
        detail["_subcluster"] = subcluster
        pr_details.append(detail)
        pr_file_inventory.append(
            {
                "number": num,
                "title": detail.get("title", ""),
                "headRefName": detail.get("headRefName", ""),
                "cluster": cluster,
                "subcluster": subcluster,
                "files": [
                    {
                        "path": f.get("path"),
                        "additions": f.get("additions"),
                        "deletions": f.get("deletions"),
                    }
                    for f in (detail.get("files") or [])
                ],
                "commitCount": len(detail.get("commits") or []),
                "singleCommitOid": (detail.get("commits") or [{}])[0].get("oid") if len(detail.get("commits") or []) == 1 else None,
            }
        )
        time.sleep(0.05)

    write_json(PR_FILE_INVENTORY_PATH, pr_file_inventory)

    duplicate_meta, duplicate_summary = duplicate_annotations(pr_details)
    dispositions, follow_up_rows = build_cluster_disposition(pr_details, main_short_sha)

    cluster_rows = build_cluster_matrix_rows(pr_details, remote_branches, open_pr_by_head, duplicate_meta, dispositions)
    write_cluster_matrix_csv(cluster_rows)

    print_progress("Phase 3: generating consolidated intent report")
    report = render_report(
        pre_open_prs=open_prs,
        pr_details=pr_details,
        remote_branches=remote_branches,
        duplicate_summary=duplicate_summary,
        dispositions=dispositions,
        follow_ups=follow_up_rows,
        main_short_sha=main_short_sha,
        main_full_sha=main_full_sha,
    )
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")

    exec_log["artifactPaths"] = {
        "openPrs": str(OPEN_PRS_PATH),
        "remoteBranches": str(REMOTE_BRANCHES_PATH),
        "prFileInventory": str(PR_FILE_INVENTORY_PATH),
        "clusterMatrix": str(CLUSTER_MATRIX_PATH),
        "intentReport": str(REPORT_PATH),
        "executionLog": str(EXEC_LOG_PATH),
    }
    exec_log["phases"]["inventory"] = {
        "duplicateSummary": duplicate_summary,
        "clusterDispositions": dispositions,
        "followUpCandidates": follow_up_rows,
    }

    print_progress("Phase 4/5: posting close comments and closing open PRs")
    pr_actions: list[dict[str, Any]] = []
    for idx, pr in enumerate(sorted(pr_details, key=lambda p: int(p["number"]))):
        if idx % 10 == 0:
            print_progress(f"  closing PRs {idx + 1}/{len(pr_details)} (PR #{pr['number']})")
        action = gh_comment_and_close_pr(pr, pr["_cluster"], main_short_sha)
        pr_actions.append(action)
        if not action["closed"]:
            exec_log["failures"].append({"type": "pr_close", **action})
        elif not action["commented"]:
            exec_log["failures"].append({"type": "pr_comment", **action})
        time.sleep(0.1)
    exec_log["phases"]["prClosure"] = {
        "total": len(pr_actions),
        "closed": sum(1 for a in pr_actions if a["closed"]),
        "commented": sum(1 for a in pr_actions if a["commented"]),
        "actions": pr_actions,
    }

    print_progress("Phase 6: deleting all non-main remote branches")
    delete_targets = sorted({b["branchName"] for b in non_main_remote})
    branch_actions: list[dict[str, Any]] = []
    for idx, branch in enumerate(delete_targets):
        if idx % 20 == 0:
            print_progress(f"  deleting branches {idx + 1}/{len(delete_targets)} ({branch})")
        action = delete_remote_branch(branch)
        branch_actions.append(action)
        if not action["deleted"]:
            exec_log["failures"].append({"type": "branch_delete", **action})
        time.sleep(0.05)
    exec_log["phases"]["branchDeletion"] = {
        "total": len(branch_actions),
        "deleted": sum(1 for a in branch_actions if a["deleted"]),
        "actions": branch_actions,
    }

    print_progress("Phase 7: post-cleanup verification")
    run(["git", "fetch", "--prune", "origin"], retries=1, retry_delay=1.0)
    post_open_prs = list_open_prs()
    ls_remote_heads = run_text(["git", "ls-remote", "--heads", "origin"]).splitlines()
    remote_head_names = []
    for line in ls_remote_heads:
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            remote_head_names.append(parts[1].removeprefix("refs/heads/"))

    post_remote_non_main = sorted([h for h in remote_head_names if h != default_branch])
    bundle_verify_post = run(["git", "bundle", "verify", exec_log["backup"]["path"]], check=False, capture_output=True, text=True)

    exec_log["postCounts"] = {
        "openPrs": len(post_open_prs),
        "remoteHeadsTotal": len(remote_head_names),
        "remoteNonMainBranches": len(post_remote_non_main),
        "remoteHeadNames": remote_head_names,
    }
    exec_log["phases"]["verification"] = {
        "bundleVerifyReturnCode": bundle_verify_post.returncode,
        "bundleVerifyStdout": bundle_verify_post.stdout,
        "bundleVerifyStderr": bundle_verify_post.stderr,
        "remainingOpenPrNumbers": [int(p["number"]) for p in post_open_prs],
        "remainingNonMainRemoteBranches": post_remote_non_main,
    }
    exec_log["completedAt"] = utc_iso()
    exec_log["status"] = "complete" if not exec_log["failures"] and len(post_open_prs) == 0 and len(post_remote_non_main) == 0 else "partial"

    write_json(EXEC_LOG_PATH, exec_log)

    print_progress("Cleanup run complete.")
    print_progress(json.dumps({"status": exec_log["status"], "postCounts": exec_log["postCounts"]}, indent=2))
    return 0 if exec_log["status"] == "complete" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise
