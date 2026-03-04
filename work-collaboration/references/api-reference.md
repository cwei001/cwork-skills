# 工作协同系统 API 参考

**版本**: v1.0 | **更新时间**: 2026-03-04

---

## 一、任务管理

### 1.1 创建任务

```http
POST /task/create
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "title": "任务标题",
 "objective": "任务目标",
 "requirements": "任务要求",
 "deadline": "2026-03-10 18:00:00",
 "priority": "high", // high/medium/low
 "assignee": "被指派人工号"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "任务ID",
   "title": "任务标题"
 }
}
```

---

### 1.2 查询任务列表

```http
POST /task/list
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "pageIndex": 1,
 "pageSize": 20,
 "status": "in_progress", // in_progress / completed / all
 "keyword": "关键词筛选（可选）"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "list": [
     {
       "id": "任务ID",
       "title": "任务标题",
       "objective": "任务目标",
       "deadline": "2026-03-10 18:00:00",
       "priority": "high",
       "assignee": "被指派人",
       "status": "in_progress"
     }
   ],
   "total": 10
 }
}
```

---

### 1.3 获取任务详情

```http
GET /task/detail/{taskId}
Headers:
 - appKey: {你的AppKey}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "任务ID",
   "title": "任务标题",
   "objective": "任务目标",
   "requirements": "任务要求",
   "deadline": "2026-03-10 18:00:00",
   "priority": "high",
   "assignee": "被指派人",
   "creator": "创建人",
   "status": "in_progress",
   "createTime": "创建时间"
 }
}
```

---

### 1.4 结束任务

```http
POST /task/complete
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "taskId": "任务ID",
 "reportId": "关联的汇报ID" // 任务必须通过汇报完成
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "任务ID",
   "status": "completed"
 }
}
```

---

## 二、汇报管理

### 2.1 提交汇报

```http
POST /work-report/report/record/submit
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "subject": "汇报标题",
 "content": "<p>汇报内容HTML</p>",
 "sendUsers": ["接收人账号1", "接收人账号2"],
 "type": 1,
 "templateId": "模板ID（可选）",
 "needDecision": false, // 是否需要领导决策
 "relatedTaskId": "关联任务ID（可选）"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "汇报记录ID",
   "subject": "汇报标题"
 }
}
```

---

### 2.2 查询我发出的汇报（发件箱）

```http
POST /work-report/report/record/outbox
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "pageIndex": 1,
 "pageSize": 20,
 "main": "标题关键词（可选）"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "list": [
     {
       "id": "汇报记录ID",
       "subject": "汇报标题",
       "content": "汇报内容（HTML）",
       "createTime": "创建时间",
       "sendUsers": ["接收人"],
       "needDecision": false
     }
   ],
   "total": 10
 }
}
```

---

### 2.3 查询我收到的汇报（收件箱）

```http
POST /work-report/report/record/inbox
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "pageIndex": 1,
 "pageSize": 20,
 "main": "标题关键词（可选）",
 "needDecision": true/false // 可选，按需筛选
}
```

**返回关键字段**：
```json
{
 "resultCode": 1,
 "data": {
   "list": [
     {
       "id": "汇报记录ID",
       "subject": "汇报标题",
       "creatorName": "创建人",
       "content": "汇报内容（HTML）",
       "createTime": "创建时间",
       "sendUsers": ["接收人"],
       "needDecision": false,
       "decisionContent": null
     }
   ],
   "total": 10
 }
}
```

---

### 2.4 回复汇报

```http
POST /work-report/report/record/reply
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "reportRecordId": "汇报ID",
 "contentHtml": "<p>回复内容</p>"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "回复记录ID"
 }
}
```

---

## 三、反馈管理

### 3.1 针对汇报发起反馈

```http
POST /feedback/create
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "reportId": "汇报ID",
 "content": "反馈内容",
 "type": "comment" // comment / escalate_to_task
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "反馈ID"
 }
}
```

---

### 3.2 将反馈升级为新任务

```http
POST /feedback/escalate
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "feedbackId": "反馈ID",
 "taskTitle": "新任务标题",
 "assignee": "被指派人"
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "新任务ID"
 }
}
```

---

### 3.3 查询汇报的反馈列表

```http
GET /feedback/list/{reportId}
Headers:
 - appKey: {你的AppKey}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "list": [
     {
       "id": "反馈ID",
       "content": "反馈内容",
       "type": "comment",
       "creatorName": "反馈人",
       "createTime": "创建时间"
     }
   ]
 }
}
```

---

## 四、决策/建议

### 4.1 在汇报上填写决策意见

```http
POST /decision/submit
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "reportId": "汇报ID",
 "decisionType": "decision", // decision / suggestion
 "content": "决策/建议内容",
 "attachment": [] // 附件（可选）
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "id": "决策ID"
 }
}
```

---

### 4.2 查询待决策的汇报

```http
POST /decision/pending
Headers:
 - appKey: {你的AppKey}
 - Content-Type: application/json
Body:
{
 "pageIndex": 1,
 "pageSize": 20
}
```

**返回**：
```json
{
 "resultCode": 1,
 "data": {
   "list": [
     {
       "id": "汇报记录ID",
       "subject": "汇报标题",
       "creatorName": "创建人",
       "content": "汇报内容",
       "createTime": "创建时间",
       "needDecision": true
     }
   ],
   "total": 5
 }
}
```

---

## 五、通用返回格式

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

## 六、完整接口清单

| 模块 | 接口 | 方法 | 路径 |
|------|------|------|------|
| 任务 | 创建任务 | POST | /task/create |
| 任务 | 查询任务列表 | POST | /task/list |
| 任务 | 获取任务详情 | GET | /task/detail/{taskId} |
| 任务 | 结束任务 | POST | /task/complete |
| 汇报 | 提交汇报 | POST | /work-report/report/record/submit |
| 汇报 | 查询发件箱 | POST | /work-report/report/record/outbox |
| 汇报 | 查询收件箱 | POST | /work-report/report/record/inbox |
| 汇报 | 回复汇报 | POST | /work-report/report/record/reply |
| 反馈 | 发起反馈 | POST | /feedback/create |
| 反馈 | 反馈升级为任务 | POST | /feedback/escalate |
| 反馈 | 查询反馈列表 | GET | /feedback/list/{reportId} |
| 决策 | 提交决策 | POST | /decision/submit |
| 决策 | 待决策列表 | POST | /decision/pending |

---

*文档版本：v1.0*
