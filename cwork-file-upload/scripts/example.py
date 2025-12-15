#!/usr/bin/env python3
"""
兼容旧文件：保留 example.py 作为入口提示。

请使用同目录下的 `upload_file.py`：
  - upload：分片上传 + 合并（可选入库）
  - download-info：取下载链接
  - file-content：取文本内容
  - recent-files：取最近上传
"""

def main():
    print("请使用 scripts/upload_file.py")
    print("示例：")
    print('  python .claude/skills/cwork-file-upload/scripts/upload_file.py upload --base-url "https://cwork-web.mediportal.com.cn" --token "XXX" --file "D:\\\\a.pdf"')

if __name__ == "__main__":
    main()
