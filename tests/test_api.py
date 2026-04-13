from pathlib import Path
from zipfile import ZipFile
import io

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.export import zip_worktree_bytes

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
            "content": "本文展示结构化映射后的论文导出流程。",
            "keywords": ["论文模板", "结构化映射"],
        },
        "abstract_en": {
            "content": "This thesis demonstrates a normalized export flow.",
            "keywords": ["thesis", "mapping"],
        },
        "body_sections": [
            {
                "id": "section-1",
                "level": 1,
                "title": "引言",
                "content": "本章介绍系统目标。",
            }
        ],
        "references": {"items": ["【1】示例作者. 论文模板实践."]},
        "acknowledgements": "感谢导师的指导。",
        "appendix": "附录 A：补充说明。",
        "warnings": [],
        "parse_errors": [],
        "capabilities": {
            "tex_zip": True,
            "pdf": False,
            "pdf_reason": "生产环境默认关闭 PDF，请导出 tex 工程 zip。",
        },
    }


def test_health_reports_capabilities_and_limits():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "capabilities" in body
    assert body["limits"]["max_docx_size_bytes"] == 4 * 1024 * 1024


def test_docx_endpoint_rejects_non_docx_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("bad.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_docx_endpoint_rejects_wrong_content_type():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("bad.docx", b"PKfake", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_docx_endpoint_rejects_empty_file():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("empty.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "CONTENT_EMPTY"


def test_docx_endpoint_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr("backend.app.main.MAX_UPLOAD_SIZE_BYTES", 8)
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("large.docx", b"PK" + b"x" * 20, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "FILE_TOO_LARGE"


def test_docx_endpoint_rejects_invalid_docx_payload():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("bad.docx", b"not-a-zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "DOCX_INVALID"


def test_docx_endpoint_reports_parse_failed_for_broken_zip():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("broken.docx", b"PKbroken-zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "PARSE_FAILED"


def test_docx_endpoint_returns_normalized_payload():
    with TestClient(app) as client:
        with FIXTURE.open("rb") as fh:
            response = client.post(
                "/api/parse/docx",
                files={"file": ("sample-thesis.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "docx"
    assert payload["abstract_cn"]["content"]
    assert payload["abstract_en"]["content"]
    assert payload["body_sections"]


def test_text_normalize_returns_body_sections():
    with TestClient(app) as client:
        response = client.post(
            "/api/normalize/text",
            json={"text": "# 引言\n\n这是正文。\n\n# 参考文献\n\n【1】示例作者. 论文模板实践."},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "text"
    assert payload["body_sections"][0]["title"] == "引言"
    assert payload["references"]["items"]


def test_text_normalize_rejects_empty_content():
    with TestClient(app) as client:
        response = client.post("/api/normalize/text", json={"text": "   \n\t"})
    assert response.status_code == 400
    assert response.json()["error_code"] == "CONTENT_EMPTY"


def test_export_texzip_returns_zip_payload():
    with TestClient(app) as client:
        response = client.post("/api/export/texzip", json=sample_payload())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    archive = ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "main.tex" in names
    assert "body/generated-body.tex" in names
    assert "cover/image.tex" in names


def test_export_texzip_rejects_missing_required_fields():
    payload = sample_payload()
    payload["metadata"]["title"] = ""
    with TestClient(app) as client:
        response = client.post("/api/export/texzip", json=payload)
    assert response.status_code == 400
    assert response.json()["error_code"] == "FIELD_MISSING"
    assert "title" in response.json()["details"]["missing_fields"]


def test_export_texzip_allows_missing_recommended_class_name():
    payload = sample_payload()
    payload["metadata"]["class_name"] = ""
    with TestClient(app) as client:
        response = client.post("/api/export/texzip", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_export_pdf_returns_disabled_when_feature_is_off(monkeypatch):
    monkeypatch.setattr("backend.app.services.pdf.ENABLE_PDF_EXPORT", False)
    with TestClient(app) as client:
        response = client.post("/api/export/pdf", json=sample_payload())
    assert response.status_code == 400
    assert response.json()["error_code"] == "PDF_DISABLED"


def test_texzip_skips_symlinks(tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "main.tex").write_text("hello", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (work_dir / "outside-link.txt").symlink_to(outside)

    archive = ZipFile(io.BytesIO(zip_worktree_bytes(work_dir)))
    assert "main.tex" in archive.namelist()
    assert "outside-link.txt" not in archive.namelist()
