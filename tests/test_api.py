from pathlib import Path
from zipfile import ZipFile
import io

from fastapi.testclient import TestClient

from backend.app.main import app

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def sample_payload():
    return {
        "source_type": "text",
        "metadata": {
            "title": "结构化映射示例论文",
            "author_name": "张三",
            "student_id": "2020123456",
            "department": "计算机学院",
            "major": "网络工程",
            "class_name": "1班",
            "advisor_name": "李老师",
            "submission_date": "2026-04-10",
        },
        "abstract_cn": {
            "content": "本文展示结构化映射后的论文导出流程，并说明如何在极简入口下完成一次完整的本科论文结构预检、风险暴露与 Word 文档导出。系统优先保障题目、摘要、正文结构与参考文献的最小可交付性，再通过统一模板输出结果。",
            "keywords": ["论文模板", "结构化映射", "Word 导出"],
        },
        "abstract_en": {
            "content": "This thesis demonstrates a minimal precheck flow that validates title, abstract, body structure, and references before exporting a formatted Word thesis document.",
            "keywords": ["thesis", "word export", "precheck"],
        },
        "body_sections": [
            {
                "id": "section-1",
                "level": 1,
                "title": "引言",
                "content": "本章介绍系统目标、输入方式与预检原则。" * 30,
            },
            {
                "id": "section-2",
                "level": 1,
                "title": "实现路径",
                "content": "实现层需要把解析结果映射为统一的论文结构对象，再由预检规则层输出阻塞项、警告项和信息项。" * 20,
            },
        ],
        "references": {"items": ["【1】示例作者. 论文模板实践."]},
        "acknowledgements": "感谢导师的指导。",
        "appendix": "附录 A：补充说明。",
        "warnings": [],
        "parse_errors": [],
        "capabilities": {
            "docx_export": True,
            "profile": "undergraduate",
        },
    }


def test_health_reports_word_capabilities_and_limits():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["template"] == "sc-th-word"
    assert body["capabilities"]["docx_export"] is True
    assert body["limits"]["max_docx_size_bytes"] == 4 * 1024 * 1024


def test_precheck_docx_rejects_non_docx_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/docx",
            files={"file": ("bad.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_precheck_docx_rejects_invalid_docx_payload():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/docx",
            files={"file": ("bad.docx", b"not-a-zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "DOCX_INVALID"


def test_precheck_docx_returns_precheck_payload():
    with TestClient(app) as client:
        with FIXTURE.open("rb") as fh:
            response = client.post(
                "/api/precheck/docx",
                files={"file": ("sample-thesis.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
    assert response.status_code == 200
    payload = response.json()
    assert payload["thesis"]["source_type"] == "docx"
    assert payload["summary"]["can_confirm"] is False
    assert any(issue["severity"] == "blocking" for issue in payload["issues"])
    assert payload["preview_blocks"]


def test_precheck_text_returns_blocking_issues_for_incomplete_content():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/text",
            json={"text": "# 引言\n\n这是正文。"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["can_confirm"] is False
    assert any(issue["severity"] == "blocking" for issue in payload["issues"])


def test_precheck_text_rejects_empty_content():
    with TestClient(app) as client:
        response = client.post("/api/precheck/text", json={"text": "   \n\t"})
    assert response.status_code == 400
    assert response.json()["error_code"] == "CONTENT_EMPTY"


def test_export_docx_rejects_blocking_payload():
    payload = sample_payload()
    payload["metadata"]["title"] = ""
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=payload)
    assert response.status_code == 400
    assert response.json()["error_code"] == "FIELD_MISSING"
    assert response.json()["details"]["blocking_count"] >= 1


def test_export_docx_returns_word_document():
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=sample_payload())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response.headers["content-disposition"] == 'attachment; filename="SC-TH-export.docx"'

    archive = ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "word/document.xml" in names
    assert "word/styles.xml" in names
    document_xml = archive.read("word/document.xml").decode("utf-8")
    assert "结构化映射示例论文" in document_xml
    assert "参考文献" in document_xml


def test_export_docx_fails_when_template_is_missing(monkeypatch):
    monkeypatch.setattr("backend.app.services.export.TEMPLATE_DOCX_PATH", Path("/tmp/missing-template.docx"))
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=sample_payload())
    assert response.status_code == 500
    assert response.json()["error_code"] == "TEMPLATE_DEPENDENCY_MISSING"
