# Claude Skills 一键安装脚本（bootstrap.ps1）
# 用法：在项目根目录的 PowerShell 中运行
#
#   # 安装所有 skill
#   irm http://192.168.3.200/claude-skill/cwork-skills/raw/branch/master/bootstrap.ps1 | iex
#
#   # 或者先下载再运行：
#   Invoke-WebRequest http://192.168.3.200/claude-skill/cwork-skills/raw/branch/master/bootstrap.ps1 -OutFile bootstrap.ps1
#   .\bootstrap.ps1
#   .\bootstrap.ps1 -Skill cwork-file-upload   # 只安装指定 skill

param(
    [string]$Skill = "",                                      # 空 = 安装全部
    [string]$Target = ".claude/skills",                        # 安装目标目录
    [string]$RepoUrl = "http://192.168.3.200/claude-skill/cwork-skills.git",
    [string]$CloneDir = "$env:TEMP\cwork-skills-bootstrap"    # 临时克隆目录
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "[ERR] $msg" -ForegroundColor Red; exit 1 }

# 1. 克隆或更新仓库到临时目录
if (Test-Path $CloneDir) {
    Write-Step "更新 skill 仓库..."
    git -C $CloneDir pull --quiet
} else {
    Write-Step "克隆 skill 仓库..."
    git clone --quiet $RepoUrl $CloneDir
}

if ($LASTEXITCODE -ne 0) { Write-Err "git 操作失败，请确认能访问 $RepoUrl" }
Write-OK "仓库就绪：$CloneDir"

# 2. 运行 install.py
$installScript = Join-Path $CloneDir "install.py"
if (!(Test-Path $installScript)) { Write-Err "install.py 不存在，仓库结构可能有误" }

if ($Skill) {
    Write-Step "安装 skill: $Skill → $Target"
    python $installScript --skill $Skill --target $Target
} else {
    Write-Step "安装所有 skill → $Target"
    python $installScript --all --target $Target
}

if ($LASTEXITCODE -ne 0) { Write-Err "安装失败" }
Write-OK "完成！skill 已安装到 $Target"
