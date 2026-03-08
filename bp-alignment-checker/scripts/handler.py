"""BP Alignment Checker handler — recursive divide-and-conquer alignment analysis.

Given a task ID, this handler:
1. Fetches the task detail and all downstream alignment links
2. Groups downstream tasks by child group
3. For EACH child group, makes an independent LLM call to analyze alignment
4. Recursively checks child tasks' own downstream alignments (all the way down)
5. Aggregates all results and makes a final LLM call for the summary report

Each LLM call only sees ONE parent-child pair, keeping token usage constant.
Progress is reported via an async callback so the user sees real-time updates.

Environment variables:
  BP_OPEN_API_BASE_URL  — API base URL (default: https://sg-al-cwork-web.mediportal.com.cn/open-api)
  BP_OPEN_API_APP_KEY   — authentication key (required)

Host dependency:
  LLM calls require the host project to provide `app.services.llm.router.LLMRouter`.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("BP_OPEN_API_BASE_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
APP_KEY = os.environ.get("BP_OPEN_API_APP_KEY", "")
TIMEOUT = 30.0

RULES_FILE = Path(__file__).parent.parent / "references" / "alignment-rules.md"
DEFAULT_MAX_DEPTH = 10
ABSOLUTE_MAX_DEPTH = 10

ProgressCallback = Callable[[str], Coroutine[Any, Any, None]]


# ─── API helpers ──────────────────────────────────────────────────

async def _api_get(path: str, params: dict | None = None) -> dict[str, Any] | None:
    url = f"{BASE_URL}{path}"
    headers = {"appKey": APP_KEY}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if data.get("resultCode") == 1:
                return data.get("data")
        except Exception as e:
            logger.error(f"BP API error: {e}")
    return None


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _extract_people(task: dict) -> dict[str, list[str]]:
    result = {}
    for tu in (task.get("taskUsers") or []):
        role = tu.get("role", "unknown")
        names = [e.get("name", "") for e in (tu.get("empList") or [])]
        if names:
            result[role] = names
    return result


def _task_summary(task: dict) -> dict:
    return {
        "id": task.get("id"),
        "name": _strip_html(task.get("name", "")),
        "fullLevelNumber": task.get("fullLevelNumber", ""),
        "groupId": task.get("groupId"),
        "measureStandard": _strip_html(task.get("measureStandard", "")),
        "description": _strip_html(task.get("description", "")),
        "planStartDate": task.get("planStartDate"),
        "planEndDate": task.get("planEndDate"),
        "people": _extract_people(task),
    }


# ─── Data fetching ────────────────────────────────────────────────

async def _fetch_goal(task_id: str) -> dict | None:
    return await _api_get("/bp/task/v2/getGoalAndKeyResult", {"id": task_id})


async def _fetch_kr(task_id: str) -> dict | None:
    return await _api_get("/bp/task/v2/getKeyResult", {"id": task_id})


async def _fetch_action(task_id: str) -> dict | None:
    return await _api_get("/bp/task/v2/getAction", {"id": task_id})


async def _auto_fetch(task_id: str) -> tuple[str, dict | None]:
    for task_type, fetcher in [
        ("目标", _fetch_goal),
        ("关键成果", _fetch_kr),
        ("关键举措", _fetch_action),
    ]:
        data = await fetcher(task_id)
        if data:
            return task_type, data
    return "unknown", None


def _collect_down_links(data: dict, task_type: str) -> list[dict]:
    links = []

    def _add(items: list | None, source_name: str, source_type: str):
        for dt in (items or []):
            links.append({
                "child_id": dt.get("id"),
                "child_name": _strip_html(dt.get("name", "")),
                "child_level": dt.get("fullLevelNumber", ""),
                "group_id": str((dt.get("groupInfo") or {}).get("id", "")),
                "group_name": (dt.get("groupInfo") or {}).get("name", ""),
                "source_name": source_name,
                "source_type": source_type,
            })

    _add(data.get("downTaskList"), _strip_html(data.get("name", "")), task_type)

    if task_type == "目标":
        for kr in (data.get("keyResults") or []):
            kr_name = _strip_html(kr.get("name", ""))
            _add(kr.get("downTaskList"), kr_name, "关键成果")
            for act in (kr.get("actions") or []):
                _add(act.get("downTaskList"), _strip_html(act.get("name", "")), "关键举措")
    elif task_type == "关键成果":
        for act in (data.get("actions") or []):
            _add(act.get("downTaskList"), _strip_html(act.get("name", "")), "关键举措")

    return links


def _group_links_by_child_group(links: list[dict]) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for lk in links:
        gid = lk["group_id"]
        if gid not in groups:
            groups[gid] = {"group_id": gid, "group_name": lk["group_name"], "links": []}
        groups[gid]["links"].append(lk)
    return groups


def _build_parent_context(data: dict, task_type: str) -> str:
    lines = [f"## 父任务（{task_type}）"]
    lines.append(f"- 名称：{_strip_html(data.get('name', ''))}")
    lines.append(f"- 编码：{data.get('fullLevelNumber', '')}")
    ms = _strip_html(data.get("measureStandard", ""))
    if ms:
        lines.append(f"- 衡量标准：{ms}")
    desc = _strip_html(data.get("description", ""))
    if desc:
        lines.append(f"- 描述：{desc}")

    people = _extract_people(data)
    if people:
        lines.append(f"- 负责人：{json.dumps(people, ensure_ascii=False)}")

    if task_type == "目标":
        for kr in (data.get("keyResults") or []):
            lines.append(f"\n### 关键成果：{_strip_html(kr.get('name', ''))}")
            kr_ms = _strip_html(kr.get("measureStandard", ""))
            if kr_ms:
                lines.append(f"  - 衡量标准：{kr_ms}")
            kr_desc = _strip_html(kr.get("description", ""))
            if kr_desc:
                lines.append(f"  - 描述：{kr_desc}")
            ap = _strip_html(kr.get("actionPlan", ""))
            if ap:
                lines.append(f"  - 行动计划：{ap}")
            for act in (kr.get("actions") or []):
                lines.append(f"  - 关键举措：{_strip_html(act.get('name', ''))}")
    elif task_type == "关键成果":
        for act in (data.get("actions") or []):
            lines.append(f"\n### 关键举措：{_strip_html(act.get('name', ''))}")
            act_ms = _strip_html(act.get("measureStandard", ""))
            if act_ms:
                lines.append(f"  - 衡量标准：{act_ms}")

    return "\n".join(lines)


async def _build_child_context(group_name: str, links: list[dict]) -> str:
    lines = [f"## 子分组：{group_name}"]
    lines.append(f"\n### 承接关系")
    for lk in links:
        lines.append(f"- 父任务的 [{lk['source_type']}]「{lk['source_name']}」 → 子任务「{lk['child_name']}」")

    lines.append(f"\n### 子任务详情")
    seen_ids = set()
    for lk in links:
        cid = lk["child_id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)

        _, child_data = await _auto_fetch(str(cid))
        if not child_data:
            lines.append(f"\n**{lk['child_name']}** (无法获取详情)")
            continue

        s = _task_summary(child_data)
        lines.append(f"\n**{s['name']}** ({s['fullLevelNumber']})")
        if s["measureStandard"]:
            lines.append(f"  - 衡量标准：{s['measureStandard']}")
        if s["description"]:
            lines.append(f"  - 描述：{s['description']}")
        if s["people"]:
            lines.append(f"  - 负责人：{json.dumps(s['people'], ensure_ascii=False)}")
        lines.append(f"  - 计划时间：{s['planStartDate']} ~ {s['planEndDate']}")

    return "\n".join(lines)


# ─── LLM call ─────────────────────────────────────────────────────

def _load_rules() -> str:
    if RULES_FILE.exists():
        return RULES_FILE.read_text(encoding="utf-8")
    return ""


PAIR_SYSTEM_PROMPT = """你是BP目标承接合理性分析专家。你的任务是分析一对"父任务-子分组"之间的承接关系是否合理。

{rules}

## 输出要求
请用以下 JSON 格式输出分析结果（不要输出其他内容）：
```json
{{
  "groupName": "子分组名称",
  "conclusion": "合理/需关注/不合理",
  "score": 8,
  "alignmentAnalysis": [
    {{
      "parentTask": "父任务名称",
      "parentType": "关键成果/关键举措",
      "childTask": "子任务名称",
      "direction": "正确/偏差",
      "contentAlignment": "良好/偏弱/缺失",
      "metricLink": "紧密/间接/缺失",
      "comment": "简要说明"
    }}
  ],
  "completenessIssues": ["未被承接的关键成果/举措..."],
  "redundancyIssues": ["冗余承接说明..."],
  "suggestions": ["改进建议1", "改进建议2"]
}}
```
score 为 1-10 分，10 分最合理。"""

SUMMARY_SYSTEM_PROMPT = """你是BP目标承接合理性分析专家。请根据以下各子分组的独立检查结果，输出一份汇总报告。

## 输出格式要求
使用 Markdown 格式输出，包含：
1. 总体评价（评分、一句话结论）
2. 各分组检查结果汇总表格
3. 关键问题清单
4. 改进建议（按优先级排序）
5. 如果有递归检查的下级结果，也要纳入汇总

注意：要具体、有据可依，不要空泛评价。"""


def _get_llm_router():
    """Lazy-load LLMRouter from the host project. Raises ImportError with a clear message."""
    try:
        from app.services.llm.router import LLMRouter
        return LLMRouter()
    except ImportError:
        raise ImportError(
            "bp-alignment-checker requires the host project to provide "
            "'app.services.llm.router.LLMRouter'. "
            "Make sure the host has an LLM router that exposes an async "
            ".chat(model_id, messages, temperature) method."
        )


async def _llm_analyze_pair(parent_ctx: str, child_ctx: str) -> dict:
    rules = _load_rules()
    system = PAIR_SYSTEM_PROMPT.format(rules=rules)
    user_msg = f"{parent_ctx}\n\n---\n\n{child_ctx}"

    router = _get_llm_router()
    try:
        result = await router.chat(
            model_id="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
        content = result.get("content", "")
        usage = result.get("usage", {})
        logger.info(
            f"Pair analysis tokens: prompt={usage.get('prompt_tokens', 0)}, "
            f"completion={usage.get('completion_tokens', 0)}"
        )
        return _parse_json_from_llm(content)
    except ImportError:
        raise
    except Exception as e:
        logger.error(f"LLM pair analysis failed: {e}")
        return {"error": str(e)}


async def _llm_summarize(parent_name: str, pair_results: list[dict]) -> str:
    user_msg = f"# 父任务：{parent_name}\n\n## 各子分组检查结果\n\n"
    user_msg += json.dumps(pair_results, ensure_ascii=False, indent=2)

    router = _get_llm_router()
    try:
        result = await router.chat(
            model_id="deepseek-chat",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
        return result.get("content", "")
    except ImportError:
        raise
    except Exception as e:
        logger.error(f"LLM summary failed: {e}")
        return f"汇总报告生成失败：{e}"


def _parse_json_from_llm(text: str) -> dict:
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"raw_response": text, "parse_error": True}


# ─── Progress helper ──────────────────────────────────────────────

async def _noop_progress(msg: str) -> None:
    pass


async def _emit(cb: ProgressCallback, msg: str) -> None:
    """Safely emit a progress message."""
    try:
        await cb(msg)
    except Exception:
        pass


# ─── Recursive check engine ──────────────────────────────────────

async def _check_task_recursive(
    task_id: str,
    task_type: str | None,
    depth: int = 0,
    max_depth: int = DEFAULT_MAX_DEPTH,
    path_label: str = "",
    progress: ProgressCallback = _noop_progress,
) -> dict:
    """Recursively check alignment for a task and all its descendants."""

    if depth >= max_depth:
        return {
            "taskId": task_id,
            "depth": depth,
            "message": f"已达到最大检查深度 ({max_depth})",
        }

    if task_type:
        fetcher = {"目标": _fetch_goal, "关键成果": _fetch_kr, "关键举措": _fetch_action}.get(task_type)
        data = await fetcher(task_id) if fetcher else None
        actual_type = task_type
    else:
        actual_type, data = await _auto_fetch(task_id)

    if not data:
        return {"error": f"Task {task_id} not found"}

    task_name = _strip_html(data.get("name", ""))
    current_label = path_label or task_name
    indent = "  " * depth
    logger.info(f"[depth={depth}] Checking: {current_label} ({task_id})")

    down_links = _collect_down_links(data, actual_type)

    if not down_links:
        return {
            "taskId": task_id,
            "taskName": task_name,
            "taskType": actual_type,
            "depth": depth,
            "childGroups": [],
            "message": "无下级承接任务（叶子节点）",
        }

    grouped = _group_links_by_child_group(down_links)
    parent_ctx = _build_parent_context(data, actual_type)
    total_groups = len(grouped)

    await _emit(progress, f"{indent}🔍 「{task_name}」有 {total_groups} 个下级承接分组，开始逐个检查...")

    pair_results = []
    for idx, (gid, ginfo) in enumerate(grouped.items(), 1):
        group_name = ginfo["group_name"]
        await _emit(progress, f"{indent}📋 [{idx}/{total_groups}] 正在分析：{task_name} → {group_name}")

        child_ctx = await _build_child_context(group_name, ginfo["links"])
        analysis = await _llm_analyze_pair(parent_ctx, child_ctx)
        analysis["groupId"] = gid
        analysis["groupName"] = group_name
        analysis["depth"] = depth

        conclusion = analysis.get("conclusion", "?")
        score = analysis.get("score", "?")
        await _emit(progress, f"{indent}  ✅ {group_name}：{conclusion}（{score}/10）")

        child_task_ids = list({lk["child_id"] for lk in ginfo["links"]})
        sub_results = []
        for cid in child_task_ids:
            sub = await _check_task_recursive(
                str(cid),
                task_type=None,
                depth=depth + 1,
                max_depth=max_depth,
                path_label=f"{current_label} → {group_name}",
                progress=progress,
            )
            if sub.get("childGroups"):
                sub_results.append(sub)

        if sub_results:
            analysis["subChecks"] = sub_results

        pair_results.append(analysis)

    await _emit(progress, f"{indent}📊 正在生成「{task_name}」的汇总报告...")
    summary = await _llm_summarize(task_name, pair_results)

    return {
        "taskId": task_id,
        "taskName": task_name,
        "taskType": actual_type,
        "depth": depth,
        "childGroups": pair_results,
        "totalPairsChecked": len(pair_results),
        "summaryReport": summary,
    }


# ─── Public handler ───────────────────────────────────────────────

async def handler(
    action: str,
    task_id: Optional[str] = None,
    task_type: Optional[str] = None,
    max_depth: Optional[int] = None,
    _progress_callback: Optional[ProgressCallback] = None,
    **kwargs,
) -> dict:
    """
    Actions:
      - check_alignment: Recursive alignment check down to leaf nodes.
        max_depth defaults to 10 (effectively unlimited).
      - collect_alignment_pairs: Quick preview of downstream groups.
    """

    progress = _progress_callback or _noop_progress

    if action == "check_alignment":
        if not task_id:
            return {"error": "task_id is required"}
        depth_limit = min(max_depth or DEFAULT_MAX_DEPTH, ABSOLUTE_MAX_DEPTH)
        return await _check_task_recursive(
            task_id, task_type, max_depth=depth_limit, progress=progress,
        )

    if action == "collect_alignment_pairs":
        if not task_id:
            return {"error": "task_id is required"}
        return await _collect_pairs_quick(task_id, task_type)

    return {
        "error": f"Unknown action: {action}",
        "available_actions": ["check_alignment", "collect_alignment_pairs"],
    }


async def _collect_pairs_quick(task_id: str, task_type: str | None) -> dict:
    if task_type:
        fetcher = {"目标": _fetch_goal, "关键成果": _fetch_kr, "关键举措": _fetch_action}.get(task_type)
        data = await fetcher(task_id) if fetcher else None
        actual_type = task_type
    else:
        actual_type, data = await _auto_fetch(task_id)

    if not data:
        return {"error": f"Task {task_id} not found"}

    task_name = _strip_html(data.get("name", ""))
    down_links = _collect_down_links(data, actual_type)

    if not down_links:
        return {
            "taskName": task_name,
            "taskType": actual_type,
            "childGroups": [],
            "message": "该任务没有下级承接任务",
        }

    grouped = _group_links_by_child_group(down_links)
    groups_summary = []
    for gid, ginfo in grouped.items():
        groups_summary.append({
            "groupId": gid,
            "groupName": ginfo["group_name"],
            "taskCount": len(ginfo["links"]),
            "tasks": [
                {"name": lk["child_name"], "source": f"{lk['source_type']}「{lk['source_name']}」"}
                for lk in ginfo["links"]
            ],
        })

    return {
        "taskName": task_name,
        "taskType": actual_type,
        "childGroups": groups_summary,
        "totalGroups": len(groups_summary),
        "totalTasks": len(down_links),
    }
