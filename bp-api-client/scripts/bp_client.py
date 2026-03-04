#!/usr/bin/env python3
"""
BP API Client - 命令行工具
用于快速查询 BP 系统数据

🔒 安全提醒：API Key 每次需通过 --key 参数提供，绝不存储到环境变量

Usage:
    # 设置环境（仅设置环境，不存储 Key）
    export BP_ENV=production  # 或 test

    # 查询周期
    python bp_client.py get-periods --key <your_api_key>

    # 查询部门分组
    python bp_client.py get-groups --period-id 2026 --key <your_api_key>

    # 查询目标列表
    python bp_client.py get-tasks --period-id 2026 --group-id xxx --key <your_api_key>

    # 查询目标详情（已知ID时跳过前面步骤）
    python bp_client.py get-goal --goal-id 2014631829004374017 --key <your_api_key>

    # 查询汇报记录
    python bp_client.py get-reports --task-id 2014631829004374017 --key <your_api_key>

    # 查询关键成果详情
    python bp_client.py get-key-result --kr-id xxx --key <your_api_key>

    # 查询关键举措详情
    python bp_client.py get-action --action-id xxx --key <your_api_key>
"""

import os
import sys
import json
import argparse
import requests
from urllib.parse import urljoin

# 环境配置
ENV_CONFIG = {
    "test": {
        "base_url": "https://cwork-api-test.xgjktech.com.cn/open-api",
        "description": "测试环境"
    },
    "production": {
        "base_url": "https://sg-al-cwork-web.mediportal.com.cn/open-api",
        "description": "生产环境"
    }
}

# 全局配置（从命令行参数设置）
_global_config = {"app_key": None, "env": "test"}

def set_global_config(app_key, env="test"):
    """设置全局配置（由主程序调用）"""
    _global_config["app_key"] = app_key
    _global_config["env"] = env

def get_config():
    """获取配置"""
    env = _global_config.get("env") or os.environ.get("BP_ENV", "test")
    app_key = _global_config.get("app_key")
    
    if not app_key:
        print("Error: 请使用 --key 参数提供 API Key")
        print("示例: python bp_client.py get-periods --key your_api_key")
        sys.exit(1)
    
    if env not in ENV_CONFIG:
        print(f"Error: 无效的环境 {env}，可选: test, production")
        sys.exit(1)
    
    return {
        "base_url": ENV_CONFIG[env]["base_url"],
        "app_key": app_key,
        "env": env
    }

def api_request(method, endpoint, params=None, data=None):
    """发送 API 请求"""
    config = get_config()
    url = urljoin(config["base_url"], endpoint)
    headers = {
        "appKey": config["app_key"],
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        else:  # POST
            resp = requests.post(url, json=data, headers=headers, timeout=30)
        
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "url": url}

def api_get(endpoint, params=None):
    """发送 GET 请求"""
    return api_request("GET", endpoint, params=params)

def api_post(endpoint, data=None):
    """发送 POST 请求"""
    return api_request("POST", endpoint, data=data)

# ==================== API 接口 ====================

def get_periods():
    """获取所有周期"""
    return api_get("/bp/period/getAllPeriod")

def get_groups(period_id):
    """获取分组树"""
    return api_get("/bp/group/getTree", params={"periodId": period_id})

def get_tasks(period_id, group_id):
    """获取任务树"""
    return api_get("/bp/task/v2/getSimpleTree", params={
        "periodId": period_id,
        "groupId": group_id
    })

def get_goal(goal_id):
    """获取目标详情（含关键成果）"""
    return api_get("/bp/task/v2/getGoalAndKeyResult", params={"id": goal_id})

def get_key_result(kr_id):
    """获取关键成果详情（含关键举措）"""
    return api_get("/bp/task/v2/getKeyResult", params={"id": kr_id})

def get_action(action_id):
    """获取关键举措详情"""
    return api_get("/bp/task/v2/getAction", params={"id": action_id})

def get_reports(task_id, page=1, size=20):
    """获取汇报记录"""
    return api_post("/bp/task/relation/pageAllReports", data={
        "taskId": task_id,
        "page": page,
        "size": size
    })

# ==================== 工作流封装 ====================

def workflow_full_query(period_id=None, group_name=None, goal_name=None):
    """
    完整工作流：从周期到目标的完整查询
    适用于不知道具体 ID 的场景
    """
    print("=== Step 1: 获取周期列表 ===")
    periods = get_periods()
    print(json.dumps(periods, indent=2, ensure_ascii=False))
    
    if not period_id:
        period_id = input("\n请输入 periodId: ").strip()
    
    print(f"\n=== Step 2: 获取分组树 (periodId={period_id}) ===")
    groups = get_groups(period_id)
    print(json.dumps(groups, indent=2, ensure_ascii=False))
    
    if not groups.get("data"):
        print("未获取到分组数据")
        return
    
    # 如果指定了部门名称，尝试找到对应 ID
    group_id = None
    if group_name:
        for g in groups.get("data", []):
            if g.get("name") == group_name:
                group_id = g.get("id")
                print(f"\n找到部门: {group_name} -> groupId={group_id}")
                break
    
    if not group_id:
        group_id = input("\n请输入 groupId: ").strip()
    
    print(f"\n=== Step 3: 获取任务树 ===")
    tasks = get_tasks(period_id, group_id)
    print(json.dumps(tasks, indent=2, ensure_ascii=False))
    
    if not tasks.get("data"):
        print("未获取到任务数据")
        return
    
    # 如果指定了目标名称，尝试找到对应 ID
    goal_id = None
    if goal_name:
        for t in tasks.get("data", []):
            if t.get("name") == goal_name:
                goal_id = t.get("id")
                print(f"\n找到目标: {goal_name} -> goalId={goal_id}")
                break
    
    if goal_id:
        print(f"\n=== Step 4: 获取目标详情 (goalId={goal_id}) ===")
        goal = get_goal(goal_id)
        print(json.dumps(goal, indent=2, ensure_ascii=False))
        
        print(f"\n=== Step 5: 获取汇报记录 ===")
        reports = get_reports(goal_id)
        print(json.dumps(reports, indent=2, ensure_ascii=False))

def quick_query_goal(goal_id):
    """
    快速查询：已知目标 ID 时的快速查询
    跳过树形遍历，直接查详情
    """
    print(f"=== 快速查询目标详情 (goalId={goal_id}) ===")
    goal = get_goal(goal_id)
    print(json.dumps(goal, indent=2, ensure_ascii=False))
    
    print(f"\n=== 查询汇报记录 ===")
    reports = get_reports(goal_id)
    print(json.dumps(reports, indent=2, ensure_ascii=False))

def quick_query_reports(task_id):
    """
    快速查询汇报：只看汇报不看详情
    """
    print(f"=== 查询汇报记录 (taskId={task_id}) ===")
    reports = get_reports(task_id)
    print(json.dumps(reports, indent=2, ensure_ascii=False))

# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(
        description="BP API Client - BP 目标管理系统查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔒 安全提醒: API Key 通过 --key 参数提供，绝不存储到环境变量

环境变量（仅用于设置环境，不存储 Key）:
    export BP_ENV=production  # 或 test

示例:
    # 完整查询流程
    python bp_client.py workflow-full --key your_api_key
    
    # 快速查询已知 ID 的目标
    python bp_client.py quick-goal --goal-id 2014631829004374017 --key your_api_key
    
    # 只查汇报
    python bp_client.py quick-reports --task-id 2014631829004374017 --key your_api_key
        """
    )
    
    # 全局参数
    parser.add_argument("--key", required=True, help="API Key（必填，仅本次使用）")
    parser.add_argument("--env", default="test", choices=["test", "production"], 
                       help="环境: test 或 production (默认: test)")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # === 工作流命令 ===
    
    # workflow-full: 完整查询流程
    p_workflow = subparsers.add_parser("workflow-full", help="完整查询流程（5步法）")
    p_workflow.add_argument("--period-id", help="周期ID（可选，不提供则交互式输入）")
    p_workflow.add_argument("--group-name", help="部门名称（可选，用于自动匹配）")
    p_workflow.add_argument("--goal-name", help="目标名称（可选，用于自动匹配）")
    
    # quick-goal: 快速查目标
    p_quick_goal = subparsers.add_parser("quick-goal", help="快速查询目标详情（已知ID时）")
    p_quick_goal.add_argument("--goal-id", required=True, help="目标ID")
    
    # quick-reports: 只查汇报
    p_quick_reports = subparsers.add_parser("quick-reports", help="只查询汇报记录")
    p_quick_reports.add_argument("--task-id", required=True, help="任务ID（目标/成果/举措ID）")
    
    # === 基础 API 命令 ===
    
    # get-periods
    subparsers.add_parser("get-periods", help="获取所有周期")
    
    # get-groups
    p_groups = subparsers.add_parser("get-groups", help="获取分组树")
    p_groups.add_argument("--period-id", required=True, help="周期ID")
    
    # get-tasks
    p_tasks = subparsers.add_parser("get-tasks", help="获取任务树")
    p_tasks.add_argument("--period-id", required=True, help="周期ID")
    p_tasks.add_argument("--group-id", required=True, help="分组ID")
    
    # get-goal
    p_goal = subparsers.add_parser("get-goal", help="获取目标详情")
    p_goal.add_argument("--goal-id", required=True, help="目标ID")
    
    # get-key-result
    p_kr = subparsers.add_parser("get-key-result", help="获取关键成果详情")
    p_kr.add_argument("--kr-id", required=True, help="关键成果ID")
    
    # get-action
    p_action = subparsers.add_parser("get-action", help="获取关键举措详情")
    p_action.add_argument("--action-id", required=True, help="关键举措ID")
    
    # get-reports
    p_reports = subparsers.add_parser("get-reports", help="获取汇报记录")
    p_reports.add_argument("--task-id", required=True, help="任务ID")
    p_reports.add_argument("--page", type=int, default=1, help="页码")
    p_reports.add_argument("--size", type=int, default=20, help="每页条数")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 设置全局配置（API Key 和 环境）
    set_global_config(args.key, args.env)
    
    # 执行命令
    if args.command == "workflow-full":
        workflow_full_query(args.period_id, args.group_name, args.goal_name)
    elif args.command == "quick-goal":
        quick_query_goal(args.goal_id)
    elif args.command == "quick-reports":
        quick_query_reports(args.task_id)
    elif args.command == "get-periods":
        result = get_periods()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-groups":
        result = get_groups(args.period_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-tasks":
        result = get_tasks(args.period_id, args.group_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-goal":
        result = get_goal(args.goal_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-key-result":
        result = get_key_result(args.kr_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-action":
        result = get_action(args.action_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "get-reports":
        result = get_reports(args.task_id, args.page, args.size)
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
