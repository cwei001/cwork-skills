"""BP Data Viewer handler — query BP business data via Open-API.

Supports seven actions mapping to the BP Open-API endpoints:
  - get_all_periods:        查询所有周期列表
  - get_group_tree:         获取某个周期下的分组树
  - get_task_tree:          获取某个分组下的任务树
  - get_goal_detail:        获取目标详情及其下所有关键成果
  - get_key_result_detail:  获取关键成果详情及其下所有关键举措
  - get_action_detail:      获取关键举措详情
  - get_task_reports:       分页查询某个任务的所有汇报

Environment variables:
  BP_OPEN_API_BASE_URL  — API base URL (default: https://sg-al-cwork-web.mediportal.com.cn/open-api)
  BP_OPEN_API_APP_KEY   — authentication key (required)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("BP_OPEN_API_BASE_URL", "https://sg-al-cwork-web.mediportal.com.cn/open-api")
APP_KEY = os.environ.get("BP_OPEN_API_APP_KEY", "")

TIMEOUT = 30.0


async def _request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: dict | None = None,
) -> dict[str, Any]:
    """Send a request to the BP Open-API and return the parsed response."""
    url = f"{BASE_URL}{path}"
    headers = {"appKey": APP_KEY}

    if not APP_KEY:
        return {"error": "BP_OPEN_API_APP_KEY is not configured. Please set it in environment variables or settings."}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if method == "GET":
                resp = await client.get(url, params=params, headers=headers)
            else:
                headers["Content-Type"] = "application/json"
                resp = await client.post(url, params=params, json=json_body, headers=headers)

            resp.raise_for_status()
            data = resp.json()

            if data.get("resultCode") != 1:
                return {"error": data.get("resultMsg", "Unknown API error"), "resultCode": data.get("resultCode")}

            return {"success": True, "data": data.get("data")}

        except httpx.HTTPStatusError as e:
            logger.error(f"BP API HTTP error: {e}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"BP API request failed: {e}")
            return {"error": str(e)}


async def handler(
    action: str,
    period_id: Optional[str] = None,
    period_name: Optional[str] = None,
    group_id: Optional[str] = None,
    task_id: Optional[str] = None,
    page_index: Optional[int] = 1,
    page_size: Optional[int] = 10,
    keyword: Optional[str] = None,
) -> dict:
    """Route to the appropriate BP Open-API call based on *action*."""

    if action == "get_all_periods":
        return await _get_all_periods(name=period_name)

    if action == "get_group_tree":
        if not period_id:
            return {"error": "period_id is required for get_group_tree"}
        return await _get_group_tree(period_id)

    if action == "get_task_tree":
        if not group_id:
            return {"error": "group_id is required for get_task_tree"}
        return await _get_task_tree(group_id)

    if action == "get_goal_detail":
        if not task_id:
            return {"error": "task_id is required for get_goal_detail"}
        return await _get_goal_detail(task_id)

    if action == "get_key_result_detail":
        if not task_id:
            return {"error": "task_id is required for get_key_result_detail"}
        return await _get_key_result_detail(task_id)

    if action == "get_action_detail":
        if not task_id:
            return {"error": "task_id is required for get_action_detail"}
        return await _get_action_detail(task_id)

    if action == "get_task_reports":
        if not task_id:
            return {"error": "task_id is required for get_task_reports"}
        return await _get_task_reports(task_id, page_index or 1, page_size or 10, keyword)

    return {"error": f"Unknown action: {action}. Available actions: get_all_periods, get_group_tree, get_task_tree, get_goal_detail, get_key_result_detail, get_action_detail, get_task_reports"}


async def _get_all_periods(name: str | None = None) -> dict:
    params = {}
    if name:
        params["name"] = name
    return await _request("GET", "/bp/period/getAllPeriod", params=params or None)


async def _get_group_tree(period_id: str) -> dict:
    return await _request("GET", "/bp/group/getTree", params={"periodId": period_id})


async def _get_task_tree(group_id: str) -> dict:
    return await _request("GET", "/bp/task/v2/getSimpleTree", params={"groupId": group_id})


async def _get_goal_detail(task_id: str) -> dict:
    return await _request("GET", "/bp/task/v2/getGoalAndKeyResult", params={"id": task_id})


async def _get_key_result_detail(task_id: str) -> dict:
    return await _request("GET", "/bp/task/v2/getKeyResult", params={"id": task_id})


async def _get_action_detail(task_id: str) -> dict:
    return await _request("GET", "/bp/task/v2/getAction", params={"id": task_id})


async def _get_task_reports(
    task_id: str,
    page_index: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
) -> dict:
    body: dict[str, Any] = {
        "taskId": task_id,
        "pageIndex": page_index,
        "pageSize": page_size,
    }
    if keyword:
        body["keyword"] = keyword
    return await _request("POST", "/bp/task/relation/pageAllReports", json_body=body)
