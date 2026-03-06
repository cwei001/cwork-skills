---
name: work-collaboration
description: 工作协同系统助手。调用《工作协同》系统API，实现任务管理、汇报提交与回复、反馈处理、决策建议等功能。使用前需获取 API Key。
---

# 工作协同系统助手

**版本**: v1.0 | **用途**: 任务管理 + 汇报 + 反馈 + 决策

---

## 一、核心能力

| 能力 | 说明 |
|------|------|
| **📋 任务管理** | 创建任务、查询任务、结束任务 |
| **📝 汇报管理** | 提交汇报、查询收/发件箱、回复汇报 |
| **💬 反馈管理** | 发起反馈、升级为任务、查询反馈 |
| **✅ 决策/建议** | 填写决策意见、查询待决策汇报 |

---

## 二、快速判断

| 用户表述 | 意图 | 后续操作 |
|---------|------|---------|
| "创建任务""指派任务" | 任务管理 | 调用 /task/create |
| "查询任务""我的任务" | 任务管理 | 调用 /task/list |
| "提交汇报""发汇报" | 汇报管理 | 调用 /work-report/report/record/submit |
| "收到的汇报""收件箱" | 汇报管理 | 调用 /work-report/report/record/inbox |
| "回复汇报" | 汇报管理 | 先查 inbox 获取 ID，再调用 reply |
| "反馈""评论" | 反馈管理 | 调用 /feedback/create |
| "决策""同意/不同意" | 决策 | 先查 inbox/pending 获取 ID，再调用 decision/submit |
| "完成任务" | 任务管理 | 先提交汇报，再调用 task/complete |

---

## 三、使用前提

| 必须信息 | 说明 |
|---------|------|
| **API Key** | 需要用户提供（每次询问，不存储） |
| **环境** | 生产环境 `sg-al-cwork-web.mediportal.com.cn` |

---

## 四、认证方式

所有请求必须携带 `appKey` Header：

```
appKey: {你的AppKey}
```

> POST 请求需额外携带 `Content-Type: application/json`

---

## 五、环境配置

| 环境 | Base URL |
|------|----------|
| **生产环境** | `https://sg-al-cwork-web.mediportal.com.cn/open-api` |

### URL 格式

```
https://{域名}/open-api/{接口地址}
```

**调用示例**（GET 请求）：
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/task/list' \
  -H 'appKey: XXXXXXXX'
```

**调用示例**（POST 请求）：
```bash
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/task/create' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"title": "任务标题", "assignee": "张三"}'
```

> 🔒 **安全提示**: API Key 仅用于单次请求，不得存储。

---

## 六、返回格式

### 成功响应
```json
{
 "resultCode": 1,
 "resultMsg": null,
 "data": { ... }
}
```

### 错误响应
```json
{
 "resultCode": 0,
 "resultMsg": "错误描述",
 "data": null
}
```

### 常见错误码

| 错误码 | 含义 | 处理方式 |
|--------|------|---------|
| 401 | AppKey无效 | 检查appKey是否正确 |
| 403 | 无权限 | 确认是否有该操作权限 |
| 404 | 资源不存在 | 检查ID是否正确 |
| 500 | 服务器错误 | 稍后重试 |

---

## 七、使用示例

### 示例 1：创建任务

**用户**：创建一个任务给张三，标题是【完成Q1销售报告】，截止3月15日，高优先级

**助手**：请提供 API Key，然后调用：

```bash
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/task/create' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "完成Q1销售报告",
    "objective": "完成2026年第一季度销售数据分析报告",
    "requirements": "包含各区销售数据、同比增长分析、下季度预测",
    "deadline": "2026-03-15 18:00:00",
    "priority": "high",
    "assignee": "张三"
  }'
```

---

### 示例 2：提交汇报

**用户**：发送汇报给李四，标题【本周工作进展】，内容是完成了客户对接和需求整理

**助手**：

```bash
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/work-report/report/record/submit' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{
    "subject": "本周工作进展",
    "content": "<p>本周完成工作：</p><p>1. 完成3家客户对接</p><p>2. 整理用户需求文档</p>",
    "sendUsers": ["李四"],
    "type": 1
  }'
```

---

### 示例 3：回复汇报

**用户**：回复汇报【月度工作总结】，说已阅，继续加油

**助手**：

```bash
# 1. 查询汇报获取ID
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/work-report/report/record/inbox' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"pageIndex": 1, "pageSize": 20, "main": "月度工作总结"}'

# 2. 回复
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/work-report/report/record/reply' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"reportRecordId": "获取到的ID", "contentHtml": "<p>已阅，继续加油！</p>"}'
```

---

### 示例 4：填写决策

**用户**：给汇报【项目方案】决策：同意立项，下周启动

**助手**：

```bash
# 1. 查询汇报获取ID
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/work-report/report/record/inbox' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"main": "项目方案", "needDecision": true}'

# 2. 提交决策
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/decision/submit' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"reportId": "汇报ID", "decisionType": "decision", "content": "同意立项，下周启动"}'
```

---

### 示例 5：完成任务

**用户**：任务【Q1销售报告】已完成，提交汇报

**助手**：

```bash
# 1. 提交汇报
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/work-report/report/record/submit' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{
    "subject": "Q1销售报告已完成",
    "content": "<p>报告已完成，请查收。</p>",
    "sendUsers": ["任务创建人"],
    "relatedTaskId": "任务ID"
  }'

# 2. 结束任务
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/task/complete' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "任务ID", "reportId": "汇报ID"}'
```

---

## 八、注意事项

1. **任务完成机制**：任务没有"直接完成"按钮，必须通过提交汇报来完成
2. **汇报可多次提交**：一个任务可以有多条汇报记录
3. **决策权限**：只有汇报的接收人可以填写决策/建议
4. **反馈升级**：反馈可以升级为新任务，形成任务链
5. **HTML格式**：汇报和回复内容支持HTML标签

---

## 九、详细文档

| 文件 | 用途 |
|------|------|
| `docs/overview.md` | 系统概述、对象说明、场景判断逻辑 |
| `references/api-reference.md` | 完整 API 接口文档 |

---

## 十、相关资源

- 接口完整文档：https://sg-al-cwork-web.mediportal.com.cn/dev-docs/web/dist/#/solutions

---

*文档版本：v1.0 | 创建时间：2026-03-04*
