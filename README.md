# Claude Skills

面向 Claude Code 的 Skill 集合，采用 **Monorepo** 统一管理。  
GitHub：[cwei001/cwork-skills](https://github.com/cwei001/cwork-skills)

## 可用 Skill

| Skill | 说明 |
|---|---|
| [bp-alignment-checker](./bp-alignment-checker/) | BP目标承接合理性检查工具：基于递归分治法，自动检查BP目标体系中所有层级的承接关系是否合理。 |
| [bp-api-client](./bp-api-client/) | BP 目标管理系统助手。支持 BP 知识问答与数据查询。 |
| [bp-data-viewer](./bp-data-viewer/) | BP目标管理数据查询工具：查询公司BP系统中的周期、分组、目标、关键成果、关键举措和汇报数据。 |
| [cwork-file-upload](./cwork-file-upload/) | Cwork 文件分片上传/秒传/断点续传与知识库入库操作 |
| [work-collaboration](./work-collaboration/) | 工作协同系统助手。调用《工作协同》系统API，实现任务管理、汇报提交与回复、反馈处理、决策建议等功能。 |

---

## 安装方式

如果您在 OpenClaw 中使用，您可以直接使用自带命令通过 URL 进行安装：

```bash
# 安装技能库
openclaw skills install https://github.com/cwei001/cwork-skills.git
```

---

## 贡献新 Skill

在仓库根目录新建子目录（目录名即 skill 名），并在其中创建 `SKILL.md`，安装工具会自动发现它。

```
my-skill/
├── SKILL.md          # 必须
├── requirements.txt  # 可选，Python 依赖
├── scripts/          # 可选，可执行脚本
└── references/       # 可选，参考文档
```
