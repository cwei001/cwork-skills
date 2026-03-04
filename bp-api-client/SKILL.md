---
name: bp-api-client
description: BP 目标管理系统助手。支持两类功能：1) BP 知识问答（概念、术语、填报流程、FAQ）；2) BP 数据查询（周期、部门、目标、汇报）。使用前需确认查询周期和获取 API Key。
---

# BP 目标管理系统助手

**版本**: v2.0 | **用途**: 知识问答 + 数据查询

---

## 一、核心能力

| 能力 | 说明 |
|------|------|
| **📚 知识问答** | BP 概念解释、术语定义、填报流程、常见问题 |
| **🔍 数据查询** | 周期、部门、目标树、目标详情、汇报记录 |

---

## 二、知识问答（无需 API）

当用户提问以下类型时，直接从文档中回答：

| 问题类型 | 示例 |
|---------|------|
| **概念解释** | "什么是 OKR？""BROW 是什么？" |
| **术语定义** | "关键成果是什么？""undertaker 是什么？" |
| **填报流程** | "怎么创建目标？""如何填写汇报？" |
| **常见问题** | "BP 和 OKR 有什么区别？""目标一定要量化吗？" |

**知识库文档**：
- `docs/concepts.md` - BP 概念术语详解
- `docs/faq.md` - 常见问题 FAQ

---

## 三、数据查询（需要 API）

### 3.1 使用前提

| 必须信息 | 说明 |
|---------|------|
| **API Key** | 需要用户提供（每次询问，不存储） |
| **周期** | 如 "2026年度"，从 `getAllPeriod` 获取 |

### 3.2 支持的查询场景

| 场景 | 说明 |
|------|------|
| 查询某部门的所有目标 | 周期 → 部门 → 任务树 |
| 查询某人的个人 BP | 周期 → 个人节点 → 任务树 |
| 查询目标/成果/举措详情 | 直接用 ID 查询 |
| 查询汇报记录 | 用任务 ID 查询汇报 |

### 3.3 标准查询流程（5步法）

```
步骤1: GET /bp/period/getAllPeriod
       → 获取 periodId（如 "2026"）
       
步骤2: GET /bp/group/getTree?periodId={periodId}
       → 获取 groupId（如 "产品部" 的 ID）
       
步骤3: GET /bp/task/v2/getSimpleTree?groupId={groupId}&periodId={periodId}
       → 获取 taskId（目标/成果/举措 ID）
       
步骤4: GET /bp/task/v2/getGoalAndKeyResult?id={goalId}
       → 获取目标详情
       
步骤5: POST /bp/task/relation/pageAllReports
       → 查询汇报记录
```

### 3.4 API 接口清单

| 接口 | 方法 | 用途 |
|------|------|------|
| `/bp/period/getAllPeriod` | GET | 查询所有周期列表 |
| `/bp/group/getTree` | GET | 获取分组树（部门） |
| `/bp/task/v2/getSimpleTree` | GET | 获取任务树（目标列表） |
| `/bp/task/v2/getGoalAndKeyResult` | GET | 获取目标详情 |
| `/bp/task/v2/getKeyResult` | GET | 获取关键成果详情 |
| `/bp/task/v2/getAction` | GET | 获取关键举措详情 |
| `/bp/task/relation/pageAllReports` | POST | 查询汇报记录 |

---

## 四、场景判断逻辑

### 4.1 快速判断

| 用户表述 | 意图 | 后续操作 |
|---------|------|---------|
| "什么是""是什么意思" | 知识问答 | 查 docs/concepts.md |
| "怎么填""如何创建" | 知识问答 | 查 docs/concepts.md 或 docs/faq.md |
| "帮我查""看一下" | 数据查询 | 调用 API |
| "BP 进展""完成情况" | 数据查询 | 调用 API |

### 4.2 特殊场景处理

**查"负责人是某某某"时**：
- 可能想看该人个人节点下的 BP
- 也可能想看该人参与的所有任务
- **必须询问用户确认**

**查"某某某的 BP"时**：
- 默认查个人节点下的目标
- 如果查不到，确认是否查的是正确的周期

---

## 五、BP 健康度分析（进阶能力）

支持对 BP 进行三层分析：

| 层级 | 分析内容 | 数据来源 |
|------|---------|---------|
| Layer 1 | 结构完整性、时间合理性、状态一致性、责任明确性 | 任务树 |
| Layer 2 | 方向一致性、衡量标准清晰度、粒度合理性 | 目标详情 |
| Layer 3 | 计划匹配度、进展一致性、风险识别 | 汇报记录 |

**详细分析框架**：见 `docs/analysis.md`

---

## 六、完整文档索引

| 文件 | 用途 |
|------|------|
| `docs/concepts.md` | BP 概念术语详解 |
| `docs/faq.md` | 常见问题 FAQ |
| `docs/analysis.md` | 三层分析框架 |
| `docs/scenarios.md` | 使用场景与判断逻辑 |
| `references/api-reference.md` | API 详细文档 |
| `scripts/bp_client.py` | Python CLI 工具 |

---

## 七、环境配置

| 环境 | Base URL |
|------|----------|
| **生产环境** | `https://sg-al-cwork-web.mediportal.com.cn/open-api` |

**认证方式**：所有请求必须携带 `appKey` Header

```
appKey: XXXXXXXX
```

> 🔒 **安全提示**: API Key 仅用于单次请求，不得存储。

---

## 八、使用示例

### 示例 1：问知识

**用户**：什么是 OKR？

**助手**：OKR（Objectives and Key Results）是目标与关键结果管理法...

（详细内容见 docs/concepts.md）

---

### 示例 2：查数据

**用户**：帮我查一下产品部的目标

**助手**：请提供 API Key 和查询周期（如 2026 年度）

**用户**：Key 是 xxx，周期是 2026

**助手**：（调用 API 查询并返回结果）

---

*文档版本：v2.0*
