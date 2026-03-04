# Claude Skills

面向 Claude Code 的 Skill 集合，采用 **Monorepo** 统一管理。每个子目录是一个独立 Skill，包含 `SKILL.md`、脚本和参考文档。

## 可用 Skill

| Skill | 说明 |
|---|---|
| [cwork-file-upload](./cwork-file-upload/) | Cwork 文件分片上传/秒传/断点续传与知识库入库操作 |

## 安装方式

> 在**项目根目录**下运行以下命令，将 skill 安装到 `.claude/skills/`。

### 选择性安装单个 skill

```bash
python path/to/claude-skill/install.py --skill cwork-file-upload --target .claude/skills
```

### 一键安装所有 skill

```bash
python path/to/claude-skill/install.py --all --target .claude/skills
```

### 查看可用 skill 列表

```bash
python path/to/claude-skill/install.py --list
```

## 贡献新 Skill

在仓库根目录新建一个子目录（目录名即 skill 名），并在其中创建 `SKILL.md`，`install.py` 会自动发现它。

推荐目录结构：

```
my-skill/
├── SKILL.md          # 必须，skill 描述与使用说明
├── requirements.txt  # 可选，Python 依赖
├── scripts/          # 可选，可执行脚本
└── references/       # 可选，参考文档
```
