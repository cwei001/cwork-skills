#!/usr/bin/env node
/**
 * cwork-skills CLI
 *
 * 用法（npx 临时运行，无需安装）：
 *   npx -y github:cwei001/cwork-skills --all
 *   npx -y github:cwei001/cwork-skills --skill cwork-file-upload
 *   npx -y github:cwei001/cwork-skills --list
 *
 * 用法（全局安装后）：
 *   npm install -g github:cwei001/cwork-skills
 *   cwork-skills --all
 *   cwork-skills --skill cwork-file-upload --target .claude/skills
 */

'use strict';

const fs = require('fs');
const path = require('path');

// 包根目录（bin/../）
const PKG_ROOT = path.resolve(__dirname, '..');

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

function log(msg) { process.stdout.write(`[*] ${msg}\n`); }
function ok(msg) { process.stdout.write(`[OK] ${msg}\n`); }
function err(msg) { process.stderr.write(`[ERR] ${msg}\n`); process.exit(1); }

/** 递归复制目录 */
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

/** 扫描包内所有 skill 目录（含 SKILL.md 的子目录） */
function discoverSkills() {
  return fs.readdirSync(PKG_ROOT, { withFileTypes: true })
    .filter(e => e.isDirectory() && !e.name.startsWith('.') && !e.name.startsWith('_'))
    .map(e => e.name)
    .filter(name => fs.existsSync(path.join(PKG_ROOT, name, 'SKILL.md')))
    .sort();
}

/** 安装单个 skill */
function installSkill(skillName, targetDir) {
  const src = path.join(PKG_ROOT, skillName);
  if (!fs.existsSync(src)) err(`skill '${skillName}' 不存在`);

  const dst = path.join(targetDir, skillName);
  const action = fs.existsSync(dst) ? 'UPDATE' : 'INSTALL';
  log(`[${action}] ${skillName} → ${dst}`);
  if (fs.existsSync(dst)) fs.rmSync(dst, { recursive: true, force: true });
  copyDir(src, dst);
  ok(`${skillName} 安装完成`);
}

// ─── 参数解析 ─────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);

function getArg(flag) {
  const idx = args.indexOf(flag);
  return idx !== -1 ? args[idx + 1] : null;
}
function hasFlag(flag) { return args.includes(flag); }

if (args.length === 0 || hasFlag('--help') || hasFlag('-h')) {
  console.log(`
cwork-skills — Claude Code Skill 安装工具

用法：
  cwork-skills --list                          列出可用 skill
  cwork-skills --all [--target <dir>]          安装全部 skill
  cwork-skills --skill <name> [--target <dir>] 安装指定 skill

选项：
  --target <dir>   安装目标目录（默认：.claude/skills）
  --list           列出可用 skill
  --all            安装全部 skill
  --skill <name>   安装指定 skill
  --help           显示帮助
`.trim());
  process.exit(0);
}

const target = getArg('--target') || '.claude/skills';
const skillName = getArg('--skill');
const all = hasFlag('--all');
const list = hasFlag('--list');

const available = discoverSkills();

// ─── 执行 ─────────────────────────────────────────────────────────────────────

if (list) {
  if (available.length === 0) {
    console.log('暂无可用 skill。');
  } else {
    console.log('可用 skill 列表：');
    available.forEach(n => console.log(`  - ${n}`));
  }
  process.exit(0);
}

const absTarget = path.resolve(target);
fs.mkdirSync(absTarget, { recursive: true });

if (all) {
  if (available.length === 0) err('暂无可用 skill');
  for (const name of available) installSkill(name, absTarget);
  ok(`全部安装完成，共 ${available.length} 个 skill → ${absTarget}`);
} else if (skillName) {
  if (!available.includes(skillName)) {
    err(`skill '${skillName}' 不存在，可用：${available.join(', ') || '（无）'}`);
  }
  installSkill(skillName, absTarget);
  ok(`安装完成 → ${absTarget}`);
} else {
  err('请指定 --all 或 --skill <name>，用 --help 查看帮助');
}
