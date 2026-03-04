# Claude Skills

面向 Claude Code 的 Skill 集合，采用 **Monorepo** 统一管理。  
私有仓库地址：`http://192.168.3.200/claude-skill/cwork-skills`

## 可用 Skill

| Skill | 说明 |
|---|---|
| [cwork-file-upload](./cwork-file-upload/) | Cwork 文件分片上传/秒传/断点续传与知识库入库操作 |

---

## 安装方式

> 以下命令均在**项目根目录**的 PowerShell 中执行。需要能访问内网 `192.168.3.200`。

### 方式一：一键安装（推荐，无需手动 clone）

```powershell
# 安装全部 skill
Invoke-WebRequest http://192.168.3.200/claude-skill/cwork-skills/raw/branch/master/bootstrap.ps1 -OutFile bootstrap.ps1; .\bootstrap.ps1

# 只安装指定 skill
.\bootstrap.ps1 -Skill cwork-file-upload
```

> 脚本会自动把仓库 clone 到 `%TEMP%\cwork-skills-bootstrap`，然后安装到 `.claude/skills/`。  
> 下次执行会自动 `git pull` 更新。

### 方式二：手动 clone 后安装

```powershell
# 克隆一次（只需做一次）
git clone http://192.168.3.200/claude-skill/cwork-skills.git

# 安装全部 skill
python cwork-skills/install.py --all --target .claude/skills

# 仅安装指定 skill
python cwork-skills/install.py --skill cwork-file-upload --target .claude/skills

# 查看可用列表
python cwork-skills/install.py --list
```

---

## 贡献新 Skill

在仓库根目录新建子目录（目录名即 skill 名），并在其中创建 `SKILL.md`，`install.py` 会自动发现它。

推荐结构：

```
my-skill/
├── SKILL.md          # 必须
├── requirements.txt  # 可选，Python 依赖
├── scripts/          # 可选，可执行脚本
└── references/       # 可选，参考文档
```
