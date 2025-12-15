# 文件上传 API 参考（Cwork）

## 概述

本文档说明系统文件上传的完整流程与相关 API 接口。文件上传采用**分片上传**机制：将大文件切成多个小分片（**每片 5MB**），以实现断点续传与秒传。所有文件最终存储在 MinIO 对象存储中。

### 核心特性

- **分片上传**：支持大文件分片上传（每片 5MB）
- **秒传功能**：基于 MD5 校验，已存在的分片可直接复用
- **断点续传**：上传中断后可继续上传（通过查询分片是否存在实现）
- **知识库集成**：支持上传后保存到个人知识库

---

## 核心概念

### 分片（Slice）

将文件按 **5MB** 固定大小切分为多个分片，每个分片独立上传，最后合并成完整文件。

### MD5 校验

每个分片上传前计算 MD5，用于：

- 检查分片是否已存在（实现秒传）
- 验证分片完整性
- 作为分片的唯一标识

### 存储类型（StorageType）

文件存储在 MinIO 对象存储中，不同环境可能使用不同存储节点，例如：

- `MINIO_SZ`：深圳节点

### resourceId

分片合并后生成的文件唯一标识，用于后续引用、下载、内容解析等。

---

## 完整流程（分片上传）

1. **文件分片**：将待上传文件按 5MB 切分
2. **遍历每个分片**：
   - 计算 MD5
   - **接口 1**：查询分片是否存在（秒传检测）
   - 若分片不存在：
     - **接口 2**：上传分片到 MinIO
     - **接口 3**：保存分片信息到文件服务，拿到 `sliceId`
   - 若分片已存在：直接复用返回的 `sliceId`
3. **接口 4**：合并文件，得到 `resourceId`
4. **可选接口 5**：保存到个人知识库，得到 `docId`

---

## 认证说明

- 除 MinIO 的 `PUT uploadUrl` 外，其它接口均需要 Header：`access-token`

---

## API 详解

### 接口 1：查询分片是否存在

**功能**：根据分片 MD5 查询分片是否已存在；若存在返回 `sliceId`，否则返回 MinIO 上传凭证。

**请求**

`GET /file/upDownload/getSliceIdByMd5V2?md5={md5}`

**请求头（示例）**

```json
{
  "access-token": "{your_token}",
  "content-type": "application/json"
}
```

**响应（分片已存在）**

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": {
    "sliceId": "1999354360580362242",
    "uploadUrl": null,
    "storageType": null,
    "fullPath": null
  }
}
```

**响应（分片不存在）**

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": {
    "sliceId": null,
    "uploadUrl": "https://minio-.../slices/202512/a550ce...?...",
    "storageType": "MINIO_SZ",
    "fullPath": "slices/202512/a550ce2d31133c012f4c4f91afdf6fa6"
  }
}
```

字段说明：

- `sliceId`：不为空表示分片已存在可复用
- `uploadUrl`：MinIO 预签名上传地址（仅当 `sliceId` 为空时返回）
- `storageType`：存储类型（接口 3 需要）
- `fullPath`：MinIO 路径（接口 3 需要）

---

### 接口 2：上传分片到 MinIO

**功能**：将分片二进制上传到 MinIO。

> 仅当接口 1 返回 `sliceId` 为空时调用。

**请求**

`PUT {uploadUrl}`  
`Content-Type: application/octet-stream`  
`Body: 分片二进制数据`

成功返回 HTTP 200，无响应体。

---

### 接口 3：保存分片信息到文件服务

**功能**：将已上传到 MinIO 的分片信息登记到文件服务，返回 `sliceId`。

> 仅当接口 1 返回 `sliceId` 为空且接口 2 上传成功后调用。

**请求**

`POST /file/upDownload/uploadFileSliceV2`

**请求体（示例）**

```json
{
  "filePath": "slices/202512/a550ce2d31133c012f4c4f91afdf6fa6",
  "md5": "a550ce2d31133c012f4c4f91afdf6fa6",
  "size": 10166,
  "storageType": "MINIO_SZ"
}
```

**响应（示例）**

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": "1999354360580362242"
}
```

---

### 接口 4：合并文件（生成 resourceId）

**功能**：将全部分片合并为完整文件，返回 `resourceId`。

**请求**

`POST /file/upDownload/saveResource`

**请求体（示例）**

```json
{
  "name": "### 完整报告.md",
  "size": 10166,
  "suffix": "md",
  "mimeType": "",
  "sliceIds": ["1999354360580362242"],
  "time": 3703
}
```

> `sliceIds` 必须按分片顺序排列。

**响应（示例）**

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": "1999354362958336001"
}
```

---

### 接口 5：保存到个人知识库（可选）

**请求**

`POST /document-database/project/personal/saveFile`

**请求体（示例）**

```json
{
  "name": "### 完整报告.md",
  "parentId": 0,
  "resourceId": "1999354362958336001",
  "size": 10166,
  "suffix": "md",
  "type": 2
}
```

**响应（示例）**

```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": "1999354380628922369"
}
```

---

### 接口 6：获取文件内容

**地址**：`GET /file-convert/api/getFileContent`  
**参数**：

- `resourceId`：必填
- `parseImage`：可选（对 pdf/ppt/图片有效）

响应字段示例：

```json
{
  "errorEmg": "",
  "failureCount": 0,
  "resourceId": "",
  "status": 0,
  "successCount": 0,
  "totalCount": 0
}
```

---

### 接口 7：【个人知识库】获取我最新上传的文件

**地址**：`POST /document-database/project/personal/getRecentFiles`  
**query 参数**：`limit`、`searchKey`（均可选）

响应示例（数组）：

```json
[
  {
    "id": 123,
    "name": "example.txt",
    "parentId": 0,
    "projectId": 0,
    "resourceId": 456,
    "size": 1024,
    "suffix": "txt",
    "type": 2,
    "createTime": 1678888888000,
    "ancestorIds": ""
  }
]
```

---

### 接口 8：根据 resourceId 获取下载信息

**地址**：`GET /file/upDownload/getDownloadInfo`  
**query 参数**：

- `resourceId`
- `validityType`：1=7天，2=15秒，3=60分钟（默认）
- `forceDownload`：是否强制下载

响应示例：

```json
{
  "downloadUrl": "https://...",
  "fileName": "example.png",
  "resourceId": 123,
  "size": 1024,
  "suffix": "png",
  "thumbnailUrl": "https://..."
}
```

---

## 常见注意事项（摘要）

- 分片大小固定 5MB
- MD5 必须准确，否则秒传失效
- 合并时 `sliceIds` 顺序必须与原文件分片顺序一致
- 除 MinIO `PUT uploadUrl` 外都需要 `access-token`
- `uploadUrl` 有有效期，超时需重新获取
