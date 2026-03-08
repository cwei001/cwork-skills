---
name: bp-alignment-checker
description: >-
  BP目标承接合理性检查工具：基于递归分治法，自动检查BP目标体系中所有层级的承接关系是否合理。
  给定一个任务ID，自动向下递归遍历所有子孙承接链，对每一对"父任务-子分组"独立调用AI分析，
  最终汇总生成完整的检查报告。支持从集团目标一直检查到个人目标。
  Use when the user wants to check whether the alignment/inheritance relationships
  between BP tasks across all levels are reasonable.
category: business
enabled_by_default: true
metadata:
  author: built-in
  version: "2.0"
  parameters:
    type: object
    properties:
      action:
        type: string
        enum:
          - check_alignment
          - collect_alignment_pairs
        description: >-
          check_alignment: 完整的递归承接检查。自动遍历所有下级承接，逐对AI分析，生成汇总报告;
          collect_alignment_pairs: 快速预览。只收集下级承接分组概览，不执行AI分析，用于确认检查范围
      task_id:
        type: string
        description: 任务ID（目标/关键成果/关键举措）。不要转换类型，保持字符串原样传递。
      task_type:
        type: string
        enum:
          - 目标
          - 关键成果
          - 关键举措
        description: 任务类型，可选。不传会自动探测。
      max_depth:
        type: integer
        description: >-
          递归检查深度，默认10（递归到底，直到没有下级承接为止）。
          如果用户只想检查某一层，可以指定较小的值。最大10。
    required:
      - action
      - task_id
  i18n:
    zh-CN:
      display_name: BP承接检查
      description: >-
        递归检查BP目标体系中所有层级的承接关系是否合理。
        基于分治法逐层逐分组独立AI分析，自动生成完整检查报告。
      category: 业务
    en-US:
      display_name: BP Alignment Checker
      description: >-
        Recursively check BP task alignment across all levels.
        Uses divide-and-conquer with independent AI analysis per pair.
      category: Business
---

# BP目标承接合理性检查助手

你是 BP 目标承接合理性检查助手。当用户要求检查某个任务的承接合理性时，调用此工具。

## 使用方式

### 完整检查（推荐）
当用户说"检查某目标的承接是否合理"时，调用 `check_alignment`：
- 工具会自动递归检查下级承接关系，深度由 `max_depth` 控制
- 每一对"父任务-子分组"由独立的AI分析，token 恒定可控
- 最终返回包含所有层级分析结果的汇总报告
- **这是一次工具调用，内部自动完成所有分析**
- **默认 max_depth=1**（只检查直接下级），用户可要求检查更深层级

### 递归深度说明
- 默认递归到底（max_depth=10），自动检查所有层级直到叶子节点
- 检查过程中会实时推送进度信息，用户可以看到当前正在检查哪个节点
- 如果用户只想检查某一层，可以指定 `max_depth=1`（只检查直接下级）

### 快速预览
如果用户只想先看看有哪些承接关系，调用 `collect_alignment_pairs`：
- 只返回下级承接分组概览，不执行AI分析
- 用于确认检查范围后再决定是否执行完整检查

## 重要约束

- 所有 ID 参数保持字符串原样传递，**严禁 parseInt 或 Number 转换**
- 如果用户只给了任务名称没给 ID，需要先用 `bp-data-viewer` 查找对应的 task_id
- 如果不确定周期或分组，向用户确认
- 工具返回的 `summaryReport` 是完整的 Markdown 格式报告，直接展示给用户即可
- 如果检查范围很大（多层级多分组），提前告知用户可能需要等待
