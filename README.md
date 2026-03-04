# Claude Skills

面向 Claude Code 的 Skill 集合，采用 **Monorepo** 统一管理。  
私有仓库地址：`http://192.168.3.200/claude-skill/cwork-skills`

## 可用 Skill

| Skill | 说明 |
|---|---|
| [cwork-file-upload](./cwork-file-upload/) | Cwork 文件分片上传/秒传/断点续传与知识库入库操作 |

---

## 安装方式

> 安装目标目录默认为 `.claude/skills`，可通过 `--target` 自定义。  
> 需要能访问内网 `192.168.3.200`。

### 方式一：npx（推荐，无需预先安装任何东西）

```bash
# 安装全部 skill
npx git+http://192.168.3.200/claude-skill/cwork-skills.git --all

# 只安装指定 skill
npx git+http://192.168.3.200/claude-skill/cwork-skills.git --skill cwork-file-upload

# 查看可用列表
npx git+http://192.168.3.200/claude-skill/cwork-skills.git --list
```

### 方式二：npm 全局安装（适合长期使用）

```bash
# 安装一次
npm install -g git+http://192.168.3.200/claude-skill/cwork-skills.git

# 之后随时使用
cwork-skills --all
cwork-skills --skill cwork-file-upload
cwork-skills --list
```

### 方式三：PowerShell 一键安装（无 Node.js 时）

```powershell
# 下载脚本
Invoke-WebRequest http://192.168.3.200/claude-skill/cwork-skills/raw/branch/master/bootstrap.ps1 -OutFile bootstrap.ps1

# 安装全部 skill
.\bootstrap.ps1

# 只安装指定 skill
.\bootstrap.ps1 -Skill cwork-file-upload
```

### 方式四：手动 clone（需要 Python）

```bash
git clone http://192.168.3.200/claude-skill/cwork-skills.git
python cwork-skills/install.py --all --target .claude/skills
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
