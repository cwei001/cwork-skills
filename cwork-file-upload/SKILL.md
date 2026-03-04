---
name: cwork-file-upload
description: Cwork 文件分片上传/秒传/断点续传与知识库入库操作指南。用于当你需要调用文件服务接口（/file/upDownload/*、/document-database/*、/file-convert/api/*）上传大文件到 MinIO 并获取 resourceId、下载信息或文本解析结果时使用。
---

# Cwork 文件上传（分片上传）

## 概述

本 Skill 解释 Cwork 文件服务的**分片上传（每片 5MB）**全流程：分片 MD5 校验 → 秒传/上传 → 保存分片 → 合并生成 `resourceId` → 可选保存到个人知识库，并提供可执行脚本帮助你从本地文件完成上传。

## 你可以用它做什么

- **实现/生成调用代码**：给前端（JS/TS）或后端（Java/Python）生成正确的调用顺序与示例代码。
- **跑脚本上传文件**：用内置 Python 脚本从本地上传文件并拿到 `resourceId`（支持秒传与断点续传逻辑）。
- **知识库相关操作**：上传后保存到个人知识库、查询最近上传、按 `resourceId` 取下载链接/取文本内容。

## 工作流（必须按顺序）

分片上传整体流程：

1. **文件分片**：固定 **5MB/片** 切分（最后一片可小于 5MB）
2. **对每个分片**：
   - 计算分片 **MD5**
   - 调用接口 1：`GET /file/upDownload/getSliceIdByMd5V2?md5=...`
     - 若返回 `sliceId` 非空：秒传复用该分片
     - 若 `sliceId` 为空：拿到 `uploadUrl/storageType/fullPath`
       - 调接口 2：`PUT {uploadUrl}` 上传二进制到 MinIO
       - 调接口 3：`POST /file/upDownload/uploadFileSliceV2` 保存分片信息拿到 `sliceId`
3. **合并文件**：接口 4：`POST /file/upDownload/saveResource` → 得到 `resourceId`
4. **可选：保存到个人知识库**：接口 5：`POST /document-database/project/personal/saveFile` → 得到 `docId`

## 快速开始（推荐用脚本）

> **路径说明**：以下命令假设本 skill 已安装到 `.claude/skills/cwork-file-upload/`。
> 若通过 `install.py` 安装，路径由工具自动处理；手动使用时请替换为实际路径。

### 依赖安装

```bash
pip install -r .claude/skills/cwork-file-upload/requirements.txt
```

### 上传并（可选）保存到知识库

```bash
python .claude/skills/cwork-file-upload/scripts/upload_file.py upload ^
  --base-url "https://cwork-web.mediportal.com.cn" ^
  --token "YOUR_ACCESS_TOKEN" ^
  --file "D:\path\to\xxx.pdf" ^
  --save-to-knowledge --parent-id 0
```

上传成功后会输出：
- **`resourceId`**：文件唯一标识（后续下载/取文本/入库都用它）
- 可选的 **`docId`**：保存到个人知识库后的文档 ID

### 取下载链接（可选）

```bash
python .claude/skills/cwork-file-upload/scripts/upload_file.py download-info ^
  --base-url "https://cwork-web.mediportal.com.cn" ^
  --token "YOUR_ACCESS_TOKEN" ^
  --resource-id 1999354362958336001
```

### 取文本内容（可选）

```bash
python .claude/skills/cwork-file-upload/scripts/upload_file.py file-content ^
  --base-url "https://cwork-web.mediportal.com.cn" ^
  --token "YOUR_ACCESS_TOKEN" ^
  --resource-id 1999354362958336001 ^
  --parse-image false
```

## 关键约束与坑位（务必遵守）

- **分片大小固定 5MB**：服务端按该规则处理，切分不一致会导致合并失败或秒传失效。
- **MD5 必须是分片二进制的 MD5**：不要对字符串/hex 再做一次 MD5。
- **`sliceIds` 顺序必须与原文件分片顺序一致**：合并时按数组顺序拼接。
- **鉴权**：除 MinIO 的 `PUT uploadUrl` 外，其它接口均需 `access-token`。
- **上传凭证有效期**：`uploadUrl` 通常带 `X-Amz-Expires=3600`，超时需重新调接口 1 获取新的 `uploadUrl`。
- **失败重试**：建议对 MinIO `PUT` 以及接口 3/4 加重试；脚本提供 `--retries`。

## 参考文档（建议按需加载）

- **完整接口说明**：见 `references/api_reference.md`

## 资源（本 Skill 内置）

- **`scripts/upload_file.py`**：可执行 CLI，支持上传/合并/入库/取下载链接/取文本/取最近上传
- **`references/api_reference.md`**：接口文档
