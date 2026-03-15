# LinkedIn Job Agent

面向个人求职者的本地 CLI 工具，管理 LinkedIn 求职全流程：导入职位、分析 JD、计算匹配度、生成 recruiter 私信、输出日报。

## 设计原则

- 不存储 LinkedIn 密码，登录由用户手动完成，CLI 复用本地 session
- 不做批量抓取或自动发送，以"工作流管理"为目标
- 所有数据本地持久化（SQLite），输出结构化、可追踪

---

## 环境要求

- Python 3.9+

---

## 安装

```bash
git clone https://github.com/GPTtang/linkedin-job-agent.git
cd linkedin-job-agent

python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
playwright install chromium
```

---

## Agent 一键运行（推荐）

设置 API Key 后，一条命令完成全流程：

```bash
export ANTHROPIC_API_KEY="your-api-key"

python main.py init
python main.py profile import ./data/resume_sample.md
python main.py jobs import ./data/jobs_sample.json
python main.py agent run
```

Agent 自动完成：LLM 分析所有 JD → LLM 匹配评分 → 为推荐职位生成个性化外联文案 → 输出日报。

```bash
# 为前 5 个匹配职位生成文案（默认 3 个）
python main.py agent run --top-n 5
```

---

## 手动命令（逐步控制）

### LLM 版命令

```bash
# LLM 分析单条 JD
python main.py jobs analyze-llm --id 1

# LLM 匹配评分
python main.py match run-llm --job-id 1

# LLM 生成个性化私信
python main.py outreach recruiter-llm --job-id 1 --save
```

### 规则版命令（无需 API Key）

```bash
python main.py jobs analyze --id 1
python main.py match run --job-id 1
python main.py outreach recruiter --job-id 1
```

---

## 快速开始

### 1. 初始化

创建本地数据库和目录结构：

```bash
python main.py init
```

生成目录：

```
storage/    # SQLite 数据库 + 浏览器 session
data/       # 存放简历和职位 JSON
reports/    # 日报输出
outreach/   # 外联文案输出
```

---

### 2. 导入简历

简历为纯文本或 Markdown 格式，工具会自动提取技能和语言：

```bash
python main.py profile import ./data/resume_sample.md
```

查看解析结果：

```bash
python main.py profile show
```

示例简历格式（`data/resume_sample.md`）：

```markdown
# Resume

AI-oriented software engineer based in Japan.

## Skills
Python, SQL, Docker, AWS, AI, LLM, MCP, Git

## Languages
Chinese, English, Japanese
```

---

### 3. 导入职位

职位数据为 JSON 数组，每条包含以下字段：

| 字段 | 说明 |
|------|------|
| `title` | 职位名称 |
| `company` | 公司名称 |
| `location` | 工作地点 |
| `source_url` | 职位链接（用于去重） |
| `raw_text` | 职位描述原文 |
| `status` | 状态，默认 `saved` |

```bash
python main.py jobs import ./data/jobs_sample.json
```

示例文件（`data/jobs_sample.json`）：

```json
[
  {
    "source": "linkedin",
    "source_url": "https://www.linkedin.com/jobs/view/example-1",
    "title": "AI Backend Engineer",
    "company": "Example AI Japan",
    "location": "Tokyo, Japan",
    "raw_text": "We are hiring an AI Backend Engineer. Requirements: Python, SQL, Docker, AWS. 3+ years experience."
  }
]
```

查看已导入职位：

```bash
python main.py jobs list
```

> 相同 `source_url` 的职位不会重复导入。

---

### 4. 分析职位 JD

从职位描述中提取技能要求、语言要求、年限、风险点：

```bash
# 分析单条
python main.py jobs analyze --id 1

# 分析全部
python main.py jobs analyze --all
```

输出字段：

| 字段 | 说明 |
|------|------|
| `required_skills` | 必须技能 |
| `preferred_skills` | 加分技能 |
| `language_requirements` | 语言要求 |
| `years_required` | 经验年限 |
| `risks` | 风险提示（如签证、高阶日语） |

---

### 5. 匹配评分

将简历技能与职位要求对比，输出匹配分和建议：

```bash
# 对单条职位评分
python main.py match run --job-id 1

# 查看所有职位评分排行
python main.py match top
```

评分规则：

| 项目 | 分值 |
|------|------|
| 基础分 | 30 |
| 命中必须技能（每项 +10，上限 40） | 0–40 |
| 命中加分技能（每项 +5，上限 15） | 0–15 |
| **满分** | **85** |

决策阈值：

| 分数 | 决策 |
|------|------|
| ≥ 80 | `apply` — 建议优先投递 |
| 60–79 | `maybe` — 优化简历后投递 |
| < 60 | `skip` — 暂不优先 |

---

### 6. 生成 Recruiter 私信

根据职位和简历自动生成英文外联文案：

```bash
# 预览
python main.py outreach recruiter --job-id 1

# 预览并保存到 outreach/ 目录
python main.py outreach recruiter --job-id 1 --save
```

输出：
- **Standard**：完整版私信
- **Shorter Version**：简短版（适合 LinkedIn 字数限制）

---

### 7. 生成日报

汇总当天导入的职位和匹配结果，保存为 Markdown：

```bash
python main.py report daily
```

报告保存在 `reports/YYYY-MM-DD.md`。

---

### 8. LinkedIn 登录管理

首次登录（会打开 Chromium 浏览器，手动完成登录后回终端按 Enter）：

```bash
python main.py auth login
```

检查当前 session 状态：

```bash
python main.py auth status
```

清除本地 session：

```bash
python main.py auth logout
```

---

## 典型工作流

```bash
# 1. 初始化（首次运行）
python main.py init

# 2. 导入简历
python main.py profile import ./data/resume_sample.md

# 3. 导入今天收集的职位
python main.py jobs import ./data/jobs_sample.json

# 4. 分析所有职位
python main.py jobs analyze --all

# 5. 对感兴趣的职位评分
python main.py match run --job-id 1

# 6. 查看评分排行
python main.py match top

# 7. 生成外联文案
python main.py outreach recruiter --job-id 1 --save

# 8. 生成日报
python main.py report daily
```

---

## 项目结构

```
linkedin-job-agent/
├── main.py                    # 入口
├── requirements.txt
├── data/
│   ├── resume_sample.md       # 示例简历
│   └── jobs_sample.json       # 示例职位数据
├── src/ljob/
│   ├── cli.py                 # CLI 命令定义
│   ├── config.py              # 路径和技能池配置
│   ├── db.py                  # 数据库初始化
│   ├── auth.py                # LinkedIn session 管理
│   ├── utils.py               # JSON 工具函数
│   └── services/
│       ├── profile_service.py # 简历解析
│       ├── jobs_service.py    # 职位导入和分析
│       ├── match_service.py   # 匹配评分
│       ├── outreach_service.py# 外联文案生成
│       └── report_service.py  # 日报生成
├── storage/                   # 数据库和浏览器 session（自动生成）
├── reports/                   # 日报输出（自动生成）
├── outreach/                  # 外联文案输出（自动生成）
└── tests/
    └── test_import_jobs.py    # 单元测试
```

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 注意事项

- `storage/` 目录包含 LinkedIn session，请勿提交到 Git（已在 `.gitignore` 中排除）
- 职位数据需要手动从 LinkedIn 复制粘贴到 JSON 文件，工具不自动抓取
- 外联文案需要手动发送，工具不自动发送消息
