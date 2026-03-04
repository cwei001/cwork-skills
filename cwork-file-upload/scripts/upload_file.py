#!/usr/bin/env python3
"""
Cwork 文件服务：分片上传/合并/入库/下载信息/取文本 CLI

用法示例：
  python upload_file.py upload --base-url https://cwork-web.mediportal.com.cn --token XXX --file D:\\a.pdf --save-to-knowledge --parent-id 0
  python upload_file.py download-info --base-url https://cwork-web.mediportal.com.cn --token XXX --resource-id 123
  python upload_file.py file-content --base-url https://cwork-web.mediportal.com.cn --token XXX --resource-id 123 --parse-image false
  python upload_file.py recent-files --base-url https://cwork-web.mediportal.com.cn --token XXX --limit 20

注意：
  - 分片大小固定 5MB（服务端规则）
  - 除 MinIO 的 PUT 预签名 URL 外，其他接口都需要 access-token
"""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


SLICE_SIZE = 5 * 1024 * 1024  # 5MB


class ApiError(RuntimeError):
    pass


def _bool_arg(v: str) -> bool:
    vv = v.strip().lower()
    if vv in {"1", "true", "t", "yes", "y"}:
        return True
    if vv in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"非法布尔值: {v}（请用 true/false）")


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _headers(token: str) -> Dict[str, str]:
    return {"access-token": token, "content-type": "application/json"}


def _check_result(resp_json: Dict[str, Any]) -> Any:
    """
    适配 cwork 通用返回：{ resultCode: 1, resultMsg: ..., data: ... }
    """
    if not isinstance(resp_json, dict):
        raise ApiError(f"响应不是 JSON 对象: {resp_json!r}")
    result_code = resp_json.get("resultCode")
    if result_code != 1:
        raise ApiError(f"接口失败 resultCode={result_code}, resultMsg={resp_json.get('resultMsg')}, raw={resp_json}")
    return resp_json.get("data")


def _md5_bytes(b: bytes) -> str:
    h = hashlib.md5()
    h.update(b)
    return h.hexdigest()


def _guess_suffix_and_mime(file_path: str) -> Tuple[str, str]:
    base = os.path.basename(file_path)
    if "." in base:
        suffix = base.rsplit(".", 1)[1]
    else:
        suffix = ""
    mime, _ = mimetypes.guess_type(base)
    return suffix, (mime or "")


@dataclass
class SliceCheckResult:
    slice_id: Optional[str]
    upload_url: Optional[str]
    storage_type: Optional[str]
    full_path: Optional[str]


class CworkFileClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60, retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retries = retries

    def _request_json(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Any:
        url = _join_url(self.base_url, path)
        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_body,
                    headers=_headers(self.token),
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_err = e
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise ApiError(f"请求失败: {method} {url} params={params} body={json_body} err={last_err}")

    def get_slice_id_by_md5_v2(self, md5: str) -> SliceCheckResult:
        raw = self._request_json("GET", "/file/upDownload/getSliceIdByMd5V2", params={"md5": md5})
        data = _check_result(raw) or {}
        return SliceCheckResult(
            slice_id=data.get("sliceId"),
            upload_url=data.get("uploadUrl"),
            storage_type=data.get("storageType"),
            full_path=data.get("fullPath"),
        )

    def upload_slice_to_minio(self, upload_url: str, content: bytes) -> None:
        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.put(
                    upload_url,
                    data=content,
                    headers={"content-type": "application/octet-stream"},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return
            except Exception as e:
                last_err = e
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise ApiError(f"MinIO 上传失败: {upload_url} err={last_err}")

    def upload_file_slice_v2(self, *, file_path: str, md5: str, size: int, storage_type: str) -> str:
        raw = self._request_json(
            "POST",
            "/file/upDownload/uploadFileSliceV2",
            json_body={"filePath": file_path, "md5": md5, "size": size, "storageType": storage_type},
        )
        data = _check_result(raw)
        if not data:
            raise ApiError(f"uploadFileSliceV2 返回空 data: {raw}")
        return str(data)

    def save_resource(
        self,
        *,
        name: str,
        size: int,
        suffix: str,
        mime_type: str,
        slice_ids: List[str],
        time_ms: int,
    ) -> str:
        raw = self._request_json(
            "POST",
            "/file/upDownload/saveResource",
            json_body={
                "name": name,
                "size": size,
                "suffix": suffix,
                "mimeType": mime_type,
                "sliceIds": slice_ids,
                "time": time_ms,
            },
        )
        data = _check_result(raw)
        if not data:
            raise ApiError(f"saveResource 返回空 data: {raw}")
        return str(data)

    def save_to_personal_knowledge(
        self,
        *,
        name: str,
        parent_id: int,
        resource_id: str,
        size: int,
        suffix: str,
        file_type: int = 2,
    ) -> str:
        raw = self._request_json(
            "POST",
            "/document-database/project/personal/saveFile",
            json_body={
                "name": name,
                "parentId": parent_id,
                "resourceId": resource_id,
                "size": size,
                "suffix": suffix,
                "type": file_type,
            },
        )
        data = _check_result(raw)
        if not data:
            raise ApiError(f"saveFile 返回空 data: {raw}")
        return str(data)

    def get_file_content(self, *, resource_id: str, parse_image: Optional[bool] = None) -> Any:
        params: Dict[str, Any] = {"resourceId": resource_id}
        if parse_image is not None:
            params["parseImage"] = parse_image
        raw = self._request_json("GET", "/file-convert/api/getFileContent", params=params)
        if isinstance(raw, dict) and "resultCode" in raw:
            return _check_result(raw)
        return raw

    def get_recent_files(self, *, limit: Optional[int] = None, search_key: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if search_key:
            params["searchKey"] = search_key
        raw = self._request_json("POST", "/document-database/project/personal/getRecentFiles", params=params)
        if isinstance(raw, dict) and "resultCode" in raw:
            return _check_result(raw)
        return raw

    def get_download_info(
        self,
        *,
        resource_id: str,
        validity_type: Optional[int] = None,
        force_download: Optional[bool] = None,
    ) -> Any:
        params: Dict[str, Any] = {"resourceId": resource_id}
        if validity_type is not None:
            params["validityType"] = validity_type
        if force_download is not None:
            params["forceDownload"] = force_download
        raw = self._request_json("GET", "/file/upDownload/getDownloadInfo", params=params)
        return _check_result(raw)


def upload_file(
    client: CworkFileClient,
    file_path: str,
    *,
    save_to_knowledge: bool,
    parent_id: int,
) -> Tuple[str, Optional[str]]:
    start = time.time()

    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    suffix, mime_type = _guess_suffix_and_mime(file_path)

    slice_ids: List[str] = []

    with open(file_path, "rb") as f:
        index = 0
        while True:
            chunk = f.read(SLICE_SIZE)
            if not chunk:
                break

            md5 = _md5_bytes(chunk)
            check = client.get_slice_id_by_md5_v2(md5)

            if check.slice_id:
                slice_id = str(check.slice_id)
                slice_ids.append(slice_id)
                print(f"[slice {index}] 秒传复用 sliceId={slice_id} md5={md5}")
            else:
                if not check.upload_url or not check.storage_type or not check.full_path:
                    raise ApiError(f"[slice {index}] 接口1返回不完整：{check}")
                print(f"[slice {index}] 需要上传 md5={md5} fullPath={check.full_path} storageType={check.storage_type}")

                client.upload_slice_to_minio(check.upload_url, chunk)
                slice_id = client.upload_file_slice_v2(
                    file_path=check.full_path,
                    md5=md5,
                    size=len(chunk),
                    storage_type=check.storage_type,
                )
                slice_ids.append(slice_id)
                print(f"[slice {index}] 上传完成 sliceId={slice_id}")

            index += 1

    time_ms = int((time.time() - start) * 1000)
    resource_id = client.save_resource(
        name=file_name,
        size=file_size,
        suffix=suffix,
        mime_type=mime_type,
        slice_ids=slice_ids,
        time_ms=time_ms,
    )
    print(f"[merge] resourceId={resource_id} slices={len(slice_ids)} timeMs={time_ms}")

    doc_id: Optional[str] = None
    if save_to_knowledge:
        doc_id = client.save_to_personal_knowledge(
            name=file_name,
            parent_id=parent_id,
            resource_id=resource_id,
            size=file_size,
            suffix=suffix,
            file_type=2,
        )
        print(f"[knowledge] docId={doc_id} parentId={parent_id}")

    return resource_id, doc_id


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="upload_file.py", description="Cwork 文件上传相关 CLI（分片上传/合并/入库/下载信息/取文本）")
    p.add_argument("--base-url", required=True, help="API Base URL，例如 https://cwork-web.mediportal.com.cn")
    p.add_argument("--token", required=True, help="工作协同 access-token")
    p.add_argument("--timeout", type=int, default=60, help="HTTP 超时时间（秒）")
    p.add_argument("--retries", type=int, default=2, help="失败重试次数（默认 2）")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_upload = sub.add_parser("upload", help="分片上传 + 合并（可选入库）")
    p_upload.add_argument("--file", required=True, help="本地文件路径")
    p_upload.add_argument("--save-to-knowledge", action="store_true", help="上传后保存到个人知识库")
    p_upload.add_argument("--parent-id", type=int, default=0, help="个人知识库 parentId（默认 0 根目录）")

    p_download = sub.add_parser("download-info", help="根据 resourceId 获取下载信息")
    p_download.add_argument("--resource-id", required=True, help="resourceId")
    p_download.add_argument("--validity-type", type=int, default=None, help="有效期类型：1=7天，2=15秒，3=60分钟(默认)")
    p_download.add_argument("--force-download", type=_bool_arg, default=None, help="是否强制下载：true/false")

    p_content = sub.add_parser("file-content", help="根据 resourceId 获取文件内容（文本解析）")
    p_content.add_argument("--resource-id", required=True, help="resourceId")
    p_content.add_argument("--parse-image", type=_bool_arg, default=None, help="是否尝试 OCR/AI 解析（对 pdf/ppt/图片有效）")

    p_recent = sub.add_parser("recent-files", help="（个人知识库）获取我最新上传的文件列表")
    p_recent.add_argument("--limit", type=int, default=None, help="限制数量")
    p_recent.add_argument("--search-key", default=None, help="搜索关键字")

    return p


def main() -> None:
    args = build_parser().parse_args()
    client = CworkFileClient(args.base_url, args.token, timeout=args.timeout, retries=args.retries)

    if args.cmd == "upload":
        resource_id, doc_id = upload_file(
            client,
            args.file,
            save_to_knowledge=args.save_to_knowledge,
            parent_id=args.parent_id,
        )
        out: Dict[str, Any] = {"resourceId": resource_id}
        if doc_id:
            out["docId"] = doc_id
        print(out)
        return

    if args.cmd == "download-info":
        data = client.get_download_info(
            resource_id=args.resource_id,
            validity_type=args.validity_type,
            force_download=args.force_download,
        )
        print(data)
        return

    if args.cmd == "file-content":
        data = client.get_file_content(resource_id=args.resource_id, parse_image=args.parse_image)
        print(data)
        return

    if args.cmd == "recent-files":
        data = client.get_recent_files(limit=args.limit, search_key=args.search_key)
        print(data)
        return

    raise SystemExit(f"未知命令: {args.cmd}")


if __name__ == "__main__":
    main()
