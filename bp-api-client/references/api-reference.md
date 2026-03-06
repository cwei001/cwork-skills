# BP 目标管理 Open API 详细文档

## 接口基础

### 环境配置

| 环境 | Base URL |
|------|----------|
| **生产环境** | `https://sg-al-cwork-web.mediportal.com.cn/open-api` |

### 认证方式

**请求头 Header**: 所有请求必须携带 `appKey`

```
appKey: XXXXXXXX
```

> ⚠️ **注意**: appKey 需要替换为实际的密钥

### URL 格式

```
https://{域名}/open-api/{接口地址}
```

**示例**:
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/v2/getGoalAndKeyResult?id=2014631829004374017' \
  -H 'appKey: XXXXXXXX'
```

---

## 完整接口列表

| # | 接口路径 | 方法 | 说明 |
|---|----------|------|------|
| 1 | `/bp/period/getAllPeriod` | GET | 查询所有周期列表 |
| 2 | `/bp/group/getTree` | GET | 获取某个周期下的分组树 |
| 3 | `/bp/task/v2/getSimpleTree` | GET | 获取某个分组下的任务树 |
| 4 | `/bp/task/v2/getGoalAndKeyResult` | GET | 获取目标详情及其下所有关键成果 |
| 5 | `/bp/task/v2/getKeyResult` | GET | 获取关键成果详情及其下所有关键举措 |
| 6 | `/bp/task/v2/getAction` | GET | 获取关键举措详情 |
| 7 | `/bp/task/relation/pageAllReports` | POST | 分页查询某个任务的所有汇报 |

---

## 标准查询流程

```
步骤1: GET /bp/period/getAllPeriod
       ↓ 获取 periodId（如 2026 年度）
       
步骤2: GET /bp/group/getTree?periodId=xxx
       ↓ 获取 groupId（如"产品部"）
       
步骤3: GET /bp/task/v2/getSimpleTree?groupId=xxx&periodId=xxx
       ↓ 获取 taskId（目标 ID）
       
步骤4: GET /bp/task/v2/getGoalAndKeyResult?id=xxx
       ↓ 查看目标详情（含成果、举措层级）
       
步骤5: POST /bp/task/relation/pageAllReports
       ↓ 查询汇报记录
```

---

## 灵活使用接口

### 根据业务需求的接口组合

**基础5步法**是最通用的查询逻辑，实际业务中可根据需求灵活组合：

| 业务场景 | 接口组合 | 说明 |
|----------|----------|------|
| **快速查看已知目标** | 4 | 已有 goalId，直接查详情 |
| **只看汇报不看详情** | 7 | 已有 taskId，直接查汇报 |
| **查看成果执行情况** | 5 → 7 | 查成果详情 + 查汇报 |
| **查看举措执行记录** | 6 → 7 | 查举措详情 + 查汇报 |
| **批量查询多个目标** | 3 → 4（循环） | 获取列表后逐个查详情 |
| **跨部门目标对比** | 2 → 3（多部门）→ 4 | 查多个部门的目标 |

### 已知 ID 的直接查询

如果已经知道具体 ID，可以跳过树形遍历，直接查询：

```bash
# 直接查目标详情
curl -X GET 'https://.../bp/task/v2/getGoalAndKeyResult?id=2014631829004374017' \
  -H 'appKey: XXXXXXXX'

# 直接查汇报
curl -X POST 'https://.../bp/task/relation/pageAllReports' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "2014631829004374017", "page": 1, "size": 20}'
```

---

## 接口详细说明

### 1. 查询周期列表

**GET** `/bp/period/getAllPeriod`

**描述**：获取系统中所有 BP 周期（如"2025年度"、"2026Q1"等）

**调用时机**：第一步调用，拿到 periodId 后才能查后续数据

**请求参数**：无

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "2026",
      "name": "2026年度",
      "status": "enabled",
      "startTime": "2026-01-01",
      "endTime": "2026-12-31"
    },
    {
      "id": "2026Q1",
      "name": "2026年第一季度",
      "status": "enabled"
    }
  ]
}
```

**关键字段提取**：`data[].id` → periodId

---

### 2. 获取分组树

**GET** `/bp/group/getTree`

**描述**：获取周期下的组织分组树（部门结构），如"产品部"、"技术部"

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| periodId | string | ✅ | 周期 ID |

**响应示例**：
```json
{
  "code": 200,
  "data": [
    {
      "id": "group_001",
      "name": "产品部",
      "type": "department",
      "children": [
        { "id": "group_001_1", "name": "产品一组" }
      ]
    },
    {
      "id": "group_002",
      "name": "技术部",
      "type": "department"
    }
  ]
}
```

**关键字段提取**：`data[].id` → groupId

---

### 3. 获取任务树

**GET** `/bp/task/v2/getSimpleTree`

**描述**：获取分组下所有目标/关键成果/关键举措的树形列表（简要信息）

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| periodId | string | ✅ | 周期 ID |
| groupId | string | ✅ | 分组 ID |

**响应示例**：
```json
{
  "code": 200,
  "data": [
    {
      "id": "task_001",
      "name": "提升用户体验",
      "type": "goal",
      "children": [
        {
          "id": "kr_001",
          "name": "NPS 提升至 50",
          "type": "keyResult"
        }
      ]
    }
  ]
}
```

**关键字段提取**：
- `data[].id` → goalId（目标 ID）
- `data[].children[].id` → keyResultId（关键成果 ID）

---

### 4. 获取目标详情

**GET** `/bp/task/v2/getGoalAndKeyResult`

**描述**：获取目标完整信息，包含其下所有关键成果

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | ✅ | 目标 ID |

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "id": "task_001",
    "name": "提升用户体验",
    "description": "通过产品优化提升用户满意度",
    "responsible": { "id": "user_001", "name": "张三" },
    "keyResults": [
      {
        "id": "kr_001",
        "name": "NPS 提升至 50",
        "target": 50,
        "current": 45,
        "unit": "分"
      }
    ]
  }
}
```

**说明**：
- 返回数据已包含关键成果列表
- 如需查看成果下的举措，可继续调接口 5

---

### 5. 获取关键成果详情

**GET** `/bp/task/v2/getKeyResult`

**描述**：获取关键成果完整信息，包含其下所有关键举措

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | ✅ | 关键成果 ID |

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "id": "kr_001",
    "name": "NPS 提升至 50",
    "actions": [
      {
        "id": "action_001",
        "name": "优化注册流程",
        "status": "in_progress"
      }
    ]
  }
}
```

---

### 6. 获取关键举措详情

**GET** `/bp/task/v2/getAction`

**描述**：获取关键举措的完整详情

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | ✅ | 关键举措 ID |

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "id": "action_001",
    "name": "优化注册流程",
    "description": "简化注册步骤至3步以内",
    "startTime": "2026-01-01",
    "endTime": "2026-03-31",
    "status": "in_progress"
  }
}
```

---

### 7. 分页查询汇报

**POST** `/bp/task/relation/pageAllReports`

**描述**：查询任务关联的所有汇报（含手动汇报和 AI 汇报）

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | string | ✅ | 任务 ID（目标/成果/举措的 ID） |
| page | number | ❌ | 页码，默认 1 |
| size | number | ❌ | 每页条数，默认 20 |

**请求体示例**：
```json
{
  "taskId": "task_001",
  "page": 1,
  "size": 10
}
```

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "total": 15,
    "pages": 2,
    "current": 1,
    "records": [
      {
        "id": "report_001",
        "type": "manual",
        "content": "本周完成用户调研",
        "createTime": "2026-02-28"
      }
    ]
  }
}
```

**说明**：可在获取到任意层级的任务 id 后独立调用

---

## 数据层级关系

```
周期 (Period)
  └── 分组/部门 (Group)
        └── 目标 (Goal)
              └── 关键成果 (KeyResult)
                    └── 关键举措 (Action)
                          └── 汇报 (Report)
```

**层级对应关系**：
- 接口 4 → 接口 5 → 接口 6：目标 → 成果 → 举措
- 接口 4 返回已包含成果列表，概览时可不调接口 5
- 接口 7 可在任意层级独立调用

---

## 典型场景示例

### 场景1：查询"产品部"的"提升用户体验"目标详情及汇报

**步骤 1 - 获取周期**：
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/period/getAllPeriod' \
  -H 'appKey: XXXXXXXX'
Response: { "data": [{ "id": "2026", "name": "2026年度" }] }
→ periodId = "2026"
```

**步骤 2 - 获取分组树**：
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/group/getTree?periodId=2026' \
  -H 'appKey: XXXXXXXX'
Response: { "data": [{ "id": "prod_dept", "name": "产品部" }] }
→ groupId = "prod_dept"
```

**步骤 3 - 获取任务树**：
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/v2/getSimpleTree?groupId=prod_dept&periodId=2026' \
  -H 'appKey: XXXXXXXX'
Response: { "data": [{ "id": "goal_123", "name": "提升用户体验" }] }
→ goalId = "goal_123"
```

**步骤 4 - 获取目标详情**：
```bash
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/v2/getGoalAndKeyResult?id=goal_123' \
  -H 'appKey: XXXXXXXX'
→ 返回完整目标信息 + 所有关键成果
```

**步骤 5 - 查询汇报记录**：
```bash
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/relation/pageAllReports' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "goal_123", "page": 1, "size": 10}'
→ 返回该目标的所有汇报
```

### 场景2：已知目标 ID，直接查询详情

```bash
# 直接查目标详情，跳过前面的步骤
curl -X GET 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/v2/getGoalAndKeyResult?id=2014631829004374017' \
  -H 'appKey: XXXXXXXX'
```

### 场景3：查询关键成果的汇报记录

```bash
# 使用关键成果 ID 查询汇报
curl -X POST 'https://sg-al-cwork-web.mediportal.com.cn/open-api/bp/task/relation/pageAllReports' \
  -H 'appKey: XXXXXXXX' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "kr_001", "page": 1, "size": 10}'
```

---

## 常用查询组合速查

| 查询目的 | 调用顺序 |
|----------|----------|
| 查看某部门所有目标列表 | 1 → 2 → 3 |
| 查看目标详情及成果 | 1 → 2 → 3 → 4 |
| 查看成果详情及举措 | 1 → 2 → 3 → 5 |
| 查看某目标的所有汇报 | 1 → 2 → 3 → 7 |
| **直接查看已知 ID 的目标详情** | **4** |
| **直接查询已知任务的汇报** | **7** |
| 查看成果执行情况 | 5 → 7 |
| 查看举措执行记录 | 6 → 7 |

---

## 注意事项

1. **认证头必须携带**: 所有请求都需要 `appKey` Header
2. **必须先拿 periodId**：大部分查询都需要 periodId 作为基础参数
3. **树形结构遍历**：groupId 和 taskId 需要从树形结构中逐级提取
4. **ID 复用**：目标、成果、举措的 ID 均可作为 taskId 查询汇报
5. **环境配置**：生产环境域名为 `sg-al-cwork-web.mediportal.com.cn`，appKey 需替换为实际密钥
6. **灵活组合**：根据业务需求灵活组合接口，不必拘泥于5步法

---

## CLI 工具使用

详见 `scripts/bp_client.py`

### 环境设置
```bash
export BP_ENV=production
```

### 快速查询
```bash
# 完整流程
python bp_client.py workflow-full

# 快速查目标（已知ID）
python bp_client.py quick-goal --goal-id 2014631829004374017

# 只查汇报
python bp_client.py quick-reports --task-id 2014631829004374017
```

---

*文档版本：v1.1*  
*关联知识库：BP 体系知识库 (../)*
