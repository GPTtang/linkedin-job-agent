---
name: linkedin-job-agent
description: AI 求职技能。帮助用户管理 LinkedIn 求职工作流，包括职位导入、JD 分析、匹配评分、私信生成、日报输出和本地登录状态检查。
---

# LinkedIn Job Agent

用于个人求职管理，不用于违规网站自动化。

## Use when
- 用户想整理 LinkedIn 求职流程
- 用户要分析职位描述
- 用户要生成 recruiter outreach
- 用户要查看本地登录状态
- 用户要生成求职日报

## Avoid
- 批量消息发送
- 批量资料抓取
- 批量访问他人主页
- 任何高风险自动化行为

## Commands

```bash
python main.py init
python main.py profile import <resume_file>
python main.py jobs import <jobs_json>
python main.py jobs analyze --id <job_id>
python main.py match run --job-id <job_id>
python main.py outreach recruiter --job-id <job_id>
python main.py report daily
python main.py auth status
```

## Expected outputs
对于岗位分析，输出：
- required skills
- preferred skills
- language requirements
- risks
- summary

对于匹配，输出：
- score
- decision
- strengths
- gaps
- risks
- next actions

对于外联文案，输出：
- 标准版
- 简短版
