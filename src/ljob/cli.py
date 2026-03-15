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
from .services.outreach_service import recruiter_message, save_recruiter_message
from .services.report_service import generate_daily_report

app = typer.Typer(help="LinkedIn Job Agent CLI")
console = Console()

profile_app = typer.Typer()
jobs_app = typer.Typer()
match_app = typer.Typer()
outreach_app = typer.Typer()
report_app = typer.Typer()
auth_app = typer.Typer()

app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")
app.add_typer(match_app, name="match")
app.add_typer(outreach_app, name="outreach")
app.add_typer(report_app, name="report")
app.add_typer(auth_app, name="auth")


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
