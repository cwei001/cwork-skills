#!/usr/bin/env python3
"""
Claude Skills 安装工具

用法：
  # 安装单个 skill 到当前项目
  python install.py --skill cwork-file-upload --target .claude/skills

  # 安装所有 skill 到当前项目
  python install.py --all --target .claude/skills

  # 列出所有可用 skill
  python install.py --list
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys


# 本脚本所在目录即为 monorepo 根目录
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def discover_skills() -> list[str]:
    """扫描仓库根目录下所有包含 SKILL.md 的子目录，返回 skill 名列表。"""
    skills = []
    for entry in sorted(os.listdir(REPO_ROOT)):
        skill_dir = os.path.join(REPO_ROOT, entry)
        if os.path.isdir(skill_dir) and not entry.startswith((".", "_")):
            if os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
                skills.append(entry)
    return skills


def install_skill(skill_name: str, target_dir: str) -> None:
    """将指定 skill 复制到 target_dir/{skill_name}。"""
    src = os.path.join(REPO_ROOT, skill_name)
    if not os.path.isdir(src):
        print(f"[ERROR] skill '{skill_name}' 不存在（路径：{src}）", file=sys.stderr)
        sys.exit(1)

    dst = os.path.join(target_dir, skill_name)

    if os.path.exists(dst):
        print(f"[UPDATE] 更新 {skill_name} → {dst}")
        shutil.rmtree(dst)
    else:
        print(f"[INSTALL] 安装 {skill_name} → {dst}")

    shutil.copytree(src, dst)
    print(f"[OK] {skill_name} 安装完成")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="install.py",
        description="Claude Skills 安装工具（Monorepo）",
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--skill", metavar="NAME", help="安装指定 skill")
    group.add_argument("--all", action="store_true", help="安装所有 skill")
    group.add_argument("--list", action="store_true", help="列出所有可用 skill")

    p.add_argument(
        "--target",
        metavar="PATH",
        default=".claude/skills",
        help="安装目标目录（默认：.claude/skills）",
    )

    args = p.parse_args()

    available = discover_skills()

    if args.list:
        if available:
            print("可用 skill 列表：")
            for name in available:
                print(f"  - {name}")
        else:
            print("暂无可用 skill。")
        return

    target = os.path.abspath(args.target)
    os.makedirs(target, exist_ok=True)

    if args.all:
        if not available:
            print("暂无可用 skill，跳过安装。")
            return
        for name in available:
            install_skill(name, target)
        print(f"\n全部安装完成，共 {len(available)} 个 skill → {target}")
    else:
        install_skill(args.skill, target)
        print(f"\n安装完成 → {target}")


if __name__ == "__main__":
    main()
