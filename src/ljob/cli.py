import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from .config import ensure_dirs
from .db import init_db
from .auth import login_linkedin, auth_status, logout_linkedin
from .services.profile_service import import_profile_from_resume, get_profile
from .services.jobs_service import import_jobs, list_jobs, analyze_job, analyze_all_jobs
from .services.match_service import run_match, top_matches
from .services.llm_service import analyze_job_with_llm, match_job_with_llm, generate_outreach_with_llm
from .services.outreach_service import recruiter_message, save_recruiter_message
from .services.report_service import generate_daily_report
from .services.linkedin_content_service import generate_linkedin_content
from .services.linkedin_automation import update_linkedin_profile, upload_linkedin_resume
from .agent import run_agent

app = typer.Typer(help="LinkedIn Job Agent CLI")
agent_app = typer.Typer()
linkedin_app = typer.Typer()
console = Console()

profile_app = typer.Typer()
jobs_app = typer.Typer()
match_app = typer.Typer()
outreach_app = typer.Typer()
report_app = typer.Typer()
auth_app = typer.Typer()

app.add_typer(agent_app, name="agent")
app.add_typer(linkedin_app, name="linkedin")
app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")
app.add_typer(match_app, name="match")
app.add_typer(outreach_app, name="outreach")
app.add_typer(report_app, name="report")
app.add_typer(auth_app, name="auth")


@agent_app.command("run")
def agent_run(top_n: int = typer.Option(3, "--top-n", help="为前 N 个匹配职位生成文案")):
    """一键运行完整 Agent 工作流（LLM 分析 → 匹配 → 外联文案 → 日报）"""
    run_agent(top_n=top_n)


@jobs_app.command("analyze-llm")
def jobs_analyze_llm(id: int = typer.Option(..., "--id", help="职位 ID")):
    """用 LLM 分析单条职位 JD"""
    console.print(f"[cyan]正在用 LLM 分析职位 {id}...[/cyan]")
    result = analyze_job_with_llm(id)
    if result is None:
        console.print(f"[red]找不到职位 ID={id}[/red]")
        raise typer.Exit(1)
    console.print(result)


@match_app.command("run-llm")
def match_run_llm(job_id: int = typer.Option(..., "--job-id")):
    """用 LLM 对单条职位进行匹配评分"""
    console.print(f"[cyan]正在用 LLM 评分职位 {job_id}...[/cyan]")
    result = match_job_with_llm(job_id)
    if result is None:
        console.print("[red]无法评分，请先导入简历并分析职位[/red]")
        raise typer.Exit(1)
    console.print(result)


@outreach_app.command("recruiter-llm")
def outreach_recruiter_llm(
    job_id: int = typer.Option(..., "--job-id"),
    save: bool = typer.Option(False),
):
    """用 LLM 生成个性化 recruiter 私信"""
    console.print(f"[cyan]正在用 LLM 生成外联文案...[/cyan]")
    result = generate_outreach_with_llm(job_id)
    if result is None:
        console.print("[red]无法生成文案，请先导入简历并分析职位[/red]")
        raise typer.Exit(1)
    console.print(result)
    if save:
        from .config import OUTREACH_DIR
        OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTREACH_DIR / f"recruiter_job_{job_id}.md"
        content = "\n".join([
            f"# {result['subject']}", "",
            "## Standard", "", result["message"], "",
            "## Shorter Version", "", result["shorter_version"], "",
        ])
        path.write_text(content, encoding="utf-8")
        console.print(f"[green]已保存：{path}[/green]")


@linkedin_app.command("generate")
def linkedin_generate():
    """用 LLM 根据简历生成优化后的 LinkedIn Headline / About / Skills，预览不更新。"""
    console.print("[cyan]正在用 LLM 生成 LinkedIn 优化内容...[/cyan]")
    content = generate_linkedin_content()
    if not content:
        console.print("[red]请先导入简历：python main.py profile import <file>[/red]")
        raise typer.Exit(1)
    console.rule("[bold]Headline[/bold]")
    console.print(content["headline"])
    console.rule("[bold]About[/bold]")
    console.print(content["about"])
    console.rule("[bold]Skills[/bold]")
    console.print(", ".join(content["skills"]))


@linkedin_app.command("sync")
def linkedin_sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="只生成内容，不更新 LinkedIn"),
):
    """
    用 LLM 优化 LinkedIn Headline 和 About，并通过浏览器自动更新。
    需要已登录：python main.py auth login
    """
    console.print("[cyan]Step 1/2  正在用 LLM 生成优化内容...[/cyan]")
    content = generate_linkedin_content()
    if not content:
        console.print("[red]请先导入简历：python main.py profile import <file>[/red]")
        raise typer.Exit(1)

    console.print("\n[bold]将更新以下内容：[/bold]")
    console.print(f"  Headline : {content['headline']}")
    console.print(f"  About    : {content['about'][:80]}...")

    if dry_run:
        console.print("\n[yellow]--dry-run 模式，跳过实际更新[/yellow]")
        console.rule("完整 About")
        console.print(content["about"])
        return

    console.print("\n[cyan]Step 2/2  正在通过浏览器更新 LinkedIn 主页...[/cyan]")
    result = update_linkedin_profile(
        headline=content["headline"],
        about=content["about"],
    )

    if result["headline_updated"]:
        console.print("[green]✓ Headline 更新成功[/green]")
    else:
        console.print("[yellow]✗ Headline 自动更新失败，请手动粘贴：[/yellow]")
        console.print(f"  {content['headline']}")

    if result["about_updated"]:
        console.print("[green]✓ About 更新成功[/green]")
    else:
        console.print("[yellow]✗ About 自动更新失败，请手动粘贴：[/yellow]")
        console.print(content["about"])

    for err in result["errors"]:
        console.print(f"[red]  {err}[/red]")


@linkedin_app.command("upload-resume")
def linkedin_upload_resume(
    file_path: str = typer.Argument(..., help="简历文件路径（.pdf / .doc / .docx）"),
):
    """
    上传简历文件到 LinkedIn Easy Apply 简历库。
    需要已登录：python main.py auth login
    """
    console.print(f"[cyan]正在上传简历：{file_path}[/cyan]")
    result = upload_linkedin_resume(file_path)

    if result["uploaded"]:
        console.print("[green]✓ 简历上传成功[/green]")
    else:
        console.print("[red]✗ 简历上传失败[/red]")

    for err in result["errors"]:
        console.print(f"[red]  {err}[/red]")


@app.command()
def init():
    ensure_dirs()
    init_db()
    console.print("[green]项目初始化完成[/green]")


@profile_app.command("import")
def profile_import(file_path: str):
    try:
        import_profile_from_resume(file_path)
        console.print(f"[green]已导入简历：{file_path}[/green]")
    except (FileNotFoundError, OSError, ValueError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@profile_app.command("show")
def profile_show():
    profile = get_profile()
    if not profile:
        console.print("[yellow]还没有导入简历[/yellow]")
        return
    console.print(profile)


@jobs_app.command("import")
def jobs_import(file_path: str):
    try:
        count = import_jobs(file_path)
        console.print(f"[green]已导入 {count} 条职位[/green]")
    except (FileNotFoundError, OSError, ValueError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@jobs_app.command("list")
def jobs_list():
    rows = list_jobs()
    table = Table(title="Jobs")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Status")
    for row in rows:
        table.add_row(str(row["id"]), row["title"], row["company"], row["location"], row["status"])
    console.print(table)


@jobs_app.command("analyze")
def jobs_analyze(
    id: Optional[int] = typer.Option(None, "--id", help="职位 ID"),
    all: bool = typer.Option(False, "--all", help="分析所有职位"),
):
    if all:
        results = analyze_all_jobs()
        table = Table(title="Analyze All Jobs")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Required Skills")
        table.add_column("Years")
        for r in results:
            parsed = r.get("parsed") or {}
            skills = ", ".join(parsed.get("required_skills", []))
            years = str(parsed.get("years_required") or "-")
            table.add_row(str(r["id"]), r["title"], skills, years)
        console.print(table)
        return
    if id is None:
        console.print("[red]请提供 --id 或使用 --all[/red]")
        raise typer.Exit(1)
    result = analyze_job(id)
    if result is None:
        console.print(f"[red]找不到职位 ID={id}[/red]")
        raise typer.Exit(1)
    console.print(result)


@match_app.command("run")
def match_run(job_id: int = typer.Option(..., "--job-id")):
    result = run_match(job_id)
    if result is None:
        console.print("[red]无法执行匹配，请先导入简历并分析职位[/red]")
        raise typer.Exit(1)
    console.print(result)


@match_app.command("top")
def match_top():
    rows = top_matches()
    table = Table(title="Top Matches")
    table.add_column("Job ID")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Score")
    table.add_column("Decision")
    for row in rows:
        table.add_row(str(row["job_id"]), row["title"], row["company"], str(row["score"]), row["decision"])
    console.print(table)


@outreach_app.command("recruiter")
def outreach_recruiter(job_id: int = typer.Option(..., "--job-id"), save: bool = typer.Option(False)):
    result = recruiter_message(job_id)
    if result is None:
        console.print("[red]无法生成文案，请先导入简历并分析职位[/red]")
        raise typer.Exit(1)
    console.print(result)
    if save:
        try:
            path = save_recruiter_message(job_id)
            console.print(f"[green]已保存：{path}[/green]")
        except OSError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)


@report_app.command("daily")
def report_daily():
    try:
        path = generate_daily_report()
        console.print(f"[green]已生成日报：{path}[/green]")
    except OSError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@auth_app.command("login")
def auth_login():
    login_linkedin()
    console.print("[green]LinkedIn 登录会话已保存[/green]")


@auth_app.command("status")
def auth_check():
    ok = auth_status()
    console.print("[green]已登录[/green]" if ok else "[yellow]未登录或会话已失效[/yellow]")


@auth_app.command("logout")
def auth_logout():
    logout_linkedin()
    console.print("[green]本地 LinkedIn 会话已清除[/green]")
