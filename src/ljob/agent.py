"""
Agent runner: one command that autonomously runs the full job search workflow.

Steps:
  1. Analyze all imported jobs using LLM
  2. Score each job against candidate profile using LLM
  3. Generate personalized outreach for top-matched jobs
  4. Produce a daily report
"""
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .services.profile_service import get_profile
from .services.jobs_service import list_jobs
from .services.llm_service import analyze_job_with_llm, match_job_with_llm, generate_outreach_with_llm
from .services.report_service import generate_daily_report
from .config import OUTREACH_DIR

console = Console()


def run_agent(top_n: int = 3) -> None:
    """
    Run the full agent pipeline end-to-end.
    top_n: number of top-matched jobs to generate outreach for.
    """
    # Pre-flight checks
    profile = get_profile()
    if not profile:
        console.print("[red]请先导入简历：python main.py profile import <file>[/red]")
        return

    jobs = list_jobs()
    if not jobs:
        console.print("[red]请先导入职位：python main.py jobs import <file>[/red]")
        return

    console.print(f"\n[bold cyan]LinkedIn Job Agent 启动[/bold cyan]")
    console.print(f"候选人：{profile['headline']}")
    console.print(f"待处理职位：{len(jobs)} 条\n")

    # ── Step 1: Analyze all jobs ─────────────────────────────────────────────
    console.print("[bold]Step 1/3  LLM 分析职位 JD[/bold]")
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
        for job in jobs:
            task = progress.add_task(f"  {job['title']} @ {job['company']}")
            analyze_job_with_llm(job["id"])
            progress.update(task, completed=True)
    console.print(f"[green]✓ 已分析 {len(jobs)} 条职位[/green]\n")

    # ── Step 2: Match scoring ────────────────────────────────────────────────
    console.print("[bold]Step 2/3  LLM 匹配评分[/bold]")
    results: list[tuple[dict, dict]] = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
        for job in jobs:
            task = progress.add_task(f"  {job['title']} @ {job['company']}")
            match = match_job_with_llm(job["id"])
            if match:
                results.append((job, match))
            progress.update(task, completed=True)
    console.print(f"[green]✓ 已评分 {len(results)} 条职位[/green]\n")

    # Sort by score descending
    results.sort(key=lambda x: x[1].get("score", 0), reverse=True)
    apply_jobs = [(j, r) for j, r in results if r.get("decision") == "apply"]
    maybe_jobs = [(j, r) for j, r in results if r.get("decision") == "maybe"]

    # ── Step 3: Generate outreach for top apply jobs ─────────────────────────
    console.print("[bold]Step 3/3  生成个性化外联文案[/bold]")
    targets = apply_jobs[:top_n]
    if not targets:
        targets = maybe_jobs[:top_n]  # fallback to maybe if no apply

    OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    outreach_count = 0
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
        for job, _ in targets:
            task = progress.add_task(f"  {job['title']} @ {job['company']}")
            outreach = generate_outreach_with_llm(job["id"])
            if outreach:
                path = OUTREACH_DIR / f"recruiter_job_{job['id']}.md"
                content = "\n".join([
                    f"# {outreach['subject']}",
                    "",
                    "## Standard",
                    "",
                    outreach["message"],
                    "",
                    "## Shorter Version",
                    "",
                    outreach["shorter_version"],
                    "",
                ])
                path.write_text(content, encoding="utf-8")
                outreach_count += 1
            progress.update(task, completed=True)
    console.print(f"[green]✓ 已生成 {outreach_count} 份外联文案[/green]\n")

    # ── Daily report ─────────────────────────────────────────────────────────
    report_path = generate_daily_report()

    # ── Summary table ─────────────────────────────────────────────────────────
    console.print("[bold green]Agent 完成！[/bold green]\n")

    table = Table(title="匹配结果")
    table.add_column("分数", style="bold")
    table.add_column("决策")
    table.add_column("职位")
    table.add_column("公司")
    for job, r in results:
        decision = r.get("decision", "skip")
        color = {"apply": "green", "maybe": "yellow", "skip": "red"}.get(decision, "white")
        table.add_row(
            str(r.get("score", 0)),
            f"[{color}]{decision}[/{color}]",
            job["title"],
            job["company"],
        )
    console.print(table)

    console.print(f"\n推荐投递：[green]{len(apply_jobs)}[/green] 条")
    console.print(f"待考虑：  [yellow]{len(maybe_jobs)}[/yellow] 条")
    console.print(f"外联文案：{outreach_count} 份 → outreach/")
    console.print(f"日报路径：{report_path}")
