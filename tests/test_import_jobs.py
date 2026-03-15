import json
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    """每个测试用独立的临时数据库和目录"""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.chdir(tmp_path)
    # 重新导入以让 config 重新计算路径
    import importlib
    import src.ljob.config as cfg
    importlib.reload(cfg)
    import src.ljob.db as db
    importlib.reload(db)
    import src.ljob.services.jobs_service as svc
    importlib.reload(svc)

    db.init_db()
    yield


def write_jobs_file(tmp_path, data) -> str:
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(p)


# ── 正常导入 ──────────────────────────────────────────────────────────────────

def test_import_basic(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    jobs = [
        {"title": "AI Engineer", "company": "Acme", "location": "Tokyo",
         "source_url": "https://example.com/job/1", "raw_text": "python llm docker"}
    ]
    count = import_jobs(write_jobs_file(tmp_path, jobs))
    assert count == 1
    rows = list_jobs()
    assert len(rows) == 1
    assert rows[0]["title"] == "AI Engineer"
    assert rows[0]["company"] == "Acme"


def test_import_multiple(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    jobs = [
        {"title": f"Job {i}", "company": "Co", "location": "Tokyo",
         "source_url": f"https://example.com/job/{i}", "raw_text": ""}
        for i in range(5)
    ]
    count = import_jobs(write_jobs_file(tmp_path, jobs))
    assert count == 5
    assert len(list_jobs()) == 5


def test_import_default_status(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    jobs = [{"title": "Dev", "company": "X", "location": "Osaka",
             "source_url": "https://example.com/1", "raw_text": ""}]
    import_jobs(write_jobs_file(tmp_path, jobs))
    assert list_jobs()[0]["status"] == "saved"


def test_import_custom_status(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    jobs = [{"title": "Dev", "company": "X", "location": "Osaka",
             "source_url": "https://example.com/2", "raw_text": "", "status": "applied"}]
    import_jobs(write_jobs_file(tmp_path, jobs))
    assert list_jobs()[0]["status"] == "applied"


# ── 去重 ──────────────────────────────────────────────────────────────────────

def test_dedup_same_source_url(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    job = {"title": "AI Eng", "company": "Co", "location": "Tokyo",
           "source_url": "https://example.com/dup", "raw_text": ""}
    import_jobs(write_jobs_file(tmp_path, [job]))
    count2 = import_jobs(write_jobs_file(tmp_path, [job]))
    assert count2 == 0          # 第二次导入被跳过
    assert len(list_jobs()) == 1


def test_dedup_different_urls(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    jobs = [
        {"title": "Job A", "company": "Co", "location": "Tokyo",
         "source_url": "https://example.com/a", "raw_text": ""},
        {"title": "Job B", "company": "Co", "location": "Tokyo",
         "source_url": "https://example.com/b", "raw_text": ""},
    ]
    count = import_jobs(write_jobs_file(tmp_path, jobs))
    assert count == 2
    assert len(list_jobs()) == 2


def test_no_source_url_always_inserted(tmp_path):
    """没有 source_url 的条目不做去重，每次都插入"""
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    job = {"title": "No URL Job", "company": "Co", "location": "Tokyo", "raw_text": ""}
    import_jobs(write_jobs_file(tmp_path, [job]))
    import_jobs(write_jobs_file(tmp_path, [job]))
    assert len(list_jobs()) == 2


# ── 错误处理 ──────────────────────────────────────────────────────────────────

def test_file_not_found(tmp_path):
    from src.ljob.services.jobs_service import import_jobs
    with pytest.raises(FileNotFoundError):
        import_jobs(str(tmp_path / "nonexistent.json"))


def test_invalid_json(tmp_path):
    from src.ljob.services.jobs_service import import_jobs
    p = tmp_path / "bad.json"
    p.write_text("not json at all", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON 格式错误"):
        import_jobs(str(p))


def test_json_not_array(tmp_path):
    from src.ljob.services.jobs_service import import_jobs
    p = tmp_path / "obj.json"
    p.write_text(json.dumps({"title": "oops"}), encoding="utf-8")
    with pytest.raises(ValueError, match="数组"):
        import_jobs(str(p))


def test_empty_array(tmp_path):
    from src.ljob.services.jobs_service import import_jobs, list_jobs
    count = import_jobs(write_jobs_file(tmp_path, []))
    assert count == 0
    assert list_jobs() == []
