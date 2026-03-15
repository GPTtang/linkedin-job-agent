# LinkedIn Job Agent

一个面向个人求职者的 CLI Agent，用来管理 LinkedIn 求职工作流：

- 导入简历
- 导入职位
- 分析职位
- 计算匹配度
- 生成 recruiter 私信
- 输出日报
- 本地持久化 LinkedIn 登录会话（手动登录，CLI 复用）
- 兼容 Claude Code / OpenClaw skills

## 设计原则

- 不把 LinkedIn 密码写进脚本
- 不做高风险网站自动化
- 以“求职工作流管理”为主，而不是“自动化 bot”
- 所有输出尽量结构化、可追踪、可复用

## 安装

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
playwright install chromium
```

## 初始化

```bash
python main.py init
```

## 导入简历

```bash
python main.py profile import ./data/resume_sample.md
python main.py profile show
```

## 导入职位

```bash
python main.py jobs import ./data/jobs_sample.json
python main.py jobs list
```

## 分析职位

```bash
python main.py jobs analyze --id 1
python main.py jobs analyze --all
```

## 匹配评分

```bash
python main.py match run --job-id 1
python main.py match top
```

## 生成 recruiter 私信

```bash
python main.py outreach recruiter --job-id 1
```

## 日报

```bash
python main.py report daily
```

## LinkedIn 登录

首次手动登录：

```bash
python main.py auth login
```

检查会话：

```bash
python main.py auth status
```

清除会话：

```bash
python main.py auth logout
```

## Claude Code / OpenClaw

### Claude Code
把 `.claude/skills/linkedin-job-agent/` 放到项目中即可。

### OpenClaw
把 `skills/linkedin-job-agent/` 放到 workspace 的 `skills/` 目录，或复制到 `~/.openclaw/skills/`。
