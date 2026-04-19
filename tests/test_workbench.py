from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.contracts import NormalizedThesis
from backend.app.main import app


def test_normalized_thesis_v2_populates_stable_blocks():
    thesis = NormalizedThesis(
        source_type="text",
        body_sections=[{"id": "section-1", "level": 1, "title": "引言", "content": "正文内容"}],
    )

    assert thesis.schema_version == "2"
    assert thesis.blocks
    assert thesis.blocks[0].id == "section-1"
    assert thesis.blocks[0].kind == "body"


def test_story2paper_mapping_does_not_make_generated_body_exportable():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/from-story2paper",
            json={
                "cover": {"title": "AI 候选结构", "school": "华南师范大学"},
                "schema_data": {
                    "title": "AI 候选结构",
                    "sections": [{"title": "引言", "content": "这是一段旧 Writer 生成的完整正文。"}],
                    "references": [],
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["can_confirm"] is False
    assert payload["thesis"]["body_sections"][0]["content"] == ""
    assert "旧 Writer 生成" not in str(payload["thesis"])


def test_project_file_parse_proposal_and_export_flow():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"title": "测试项目"}).json()
        upload = client.post(
            f"/api/projects/{project['id']}/files",
            data={"file_type": "text", "source_label": "测试"},
            files={"file": ("paper.txt", b"# \xe5\xbc\x95\xe8\xa8\x80\n\n\xe8\xbf\x99\xe6\x98\xaf\xe8\xae\xba\xe6\x96\x87\xe6\xad\xa3\xe6\x96\x87\xe5\x86\x85\xe5\xae\xb9" * 10, "text/plain")},
        )
        assert upload.status_code == 200
        file_row = upload.json()

        job = client.post(f"/api/projects/{project['id']}/parse-jobs", json={"file_id": file_row["id"]})
        assert job.status_code == 200
        assert job.json()["status"] == "completed"
        stream = client.get(f"/api/jobs/{job.json()['id']}/events/stream")
        assert stream.status_code == 200
        assert "run_completed" in stream.text

        versions = client.get(f"/api/projects/{project['id']}/versions")
        assert versions.status_code == 200
        assert versions.json()
        assert versions.json()[0]["thesis"]["schema_version"] == "2"

        proposals = client.get(f"/api/projects/{project['id']}/proposals")
        assert proposals.status_code == 200

        export = client.post(f"/api/projects/{project['id']}/exports", json={"format": "markdown"})
        assert export.status_code == 200
        assert export.json()["filename"].endswith(".md")


def test_project_defaults_and_patch_metadata():
    with TestClient(app) as client:
        project_response = client.post(
            "/api/projects",
            json={
                "title": "阶段一项目",
                "department": "软件学院",
                "major": "软件工程",
                "advisor": "李老师",
                "student_name": "张三",
                "student_id": "2020123456",
            },
        )
        assert project_response.status_code == 200
        project = project_response.json()
        assert project["school"] == "scnu"
        assert project["degree_level"] == "undergraduate"
        assert project["template_profile"] == "scnu-undergraduate"
        assert project["privacy_mode"] == "local_only"
        assert project["remote_provider_allowed"] is False

        patched = client.patch(
            f"/api/projects/{project['id']}",
            json={"writing_stage": "revision", "privacy_mode": "remote_allowed", "remote_provider_allowed": True},
        )
        assert patched.status_code == 200
        payload = patched.json()
        assert payload["writing_stage"] == "revision"
        assert payload["privacy_mode"] == "remote_allowed"
        assert payload["remote_provider_allowed"] is True

        local_only = client.patch(f"/api/projects/{project['id']}", json={"privacy_mode": "local_only", "remote_provider_allowed": True})
        assert local_only.status_code == 200
        assert local_only.json()["remote_provider_allowed"] is False


def test_project_delete_removes_export_access():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"title": "删除测试"}).json()
        upload = client.post(
            f"/api/projects/{project['id']}/files",
            data={"file_type": "text"},
            files={"file": ("paper.txt", b"# Body\n\ncontent content content content content", "text/plain")},
        ).json()
        client.post(f"/api/projects/{project['id']}/parse-jobs", json={"file_id": upload["id"]})
        export = client.post(f"/api/projects/{project['id']}/exports", json={"format": "markdown"}).json()

        delete_response = client.delete(f"/api/projects/{project['id']}")
        assert delete_response.status_code == 200

        download = client.get(f"/api/exports/{export['id']}/download")
        assert download.status_code == 404


def test_provider_config_redacts_key_and_blocks_private_base_url():
    with TestClient(app) as client:
        blocked = client.post(
            "/api/provider-configs",
            json={"provider": "openai", "model": "x", "api_key": "secret", "base_url": "http://127.0.0.1:8000"},
        )
        assert blocked.status_code == 400

        allowed = client.post(
            "/api/provider-configs",
            json={"provider": "ollama", "model": "llama", "api_key": "secret", "base_url": "http://127.0.0.1:11434", "allow_local": True},
        )
        assert allowed.status_code == 200
        assert "secret" not in allowed.text
        assert allowed.json()["has_api_key"] is True
        assert allowed.json()["allow_local"] is True

        configs = client.get("/api/provider-configs")
        assert configs.status_code == 200
        assert all("secret" not in str(item) for item in configs.json())

        verify = client.post(f"/api/provider-configs/{allowed.json()['id']}/verify")
        assert verify.status_code == 200
        assert verify.json()["verification_status"] in {"verified", "failed"}

        deleted = client.delete(f"/api/provider-configs/{allowed.json()['id']}")
        assert deleted.status_code == 200
        assert client.get("/api/provider-configs").json() == []


def test_provider_config_remote_verify_requires_key():
    with TestClient(app) as client:
        created = client.post("/api/provider-configs", json={"provider": "openai", "model": "gpt-test", "api_key": ""})
        assert created.status_code == 200
        verify = client.post(f"/api/provider-configs/{created.json()['id']}/verify")

    assert verify.status_code == 200
    assert verify.json()["verification_status"] == "failed"
    assert "API key" in verify.json()["verification_message"]


def test_access_code_guard_requires_and_accepts_code(monkeypatch):
    monkeypatch.setenv("SCNU_ACCESS_CODE", "phase-one")
    with TestClient(app) as client:
        status = client.get("/api/access-code/status")
        assert status.status_code == 200
        assert status.json() == {"required": True, "verified": False}

        blocked = client.get("/api/projects")
        assert blocked.status_code == 401

        public = client.post("/api/public/precheck/text", json={"text": "已有论文正文", "privacy_accepted": True})
        assert public.status_code == 200

        wrong = client.post("/api/access-code/verify", json={"access_code": "wrong"})
        assert wrong.status_code == 401

        verified = client.post("/api/access-code/verify", json={"access_code": "phase-one"})
        assert verified.status_code == 200
        assert verified.json()["verified"] is True

        assert client.get("/api/access-code/status").json() == {"required": True, "verified": True}
        assert client.get("/api/projects").status_code == 200


def test_project_audit_logs_are_listed():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"title": "审计日志项目"}).json()
        logs = client.get(f"/api/projects/{project['id']}/audit-logs")

    assert logs.status_code == 200
    payload = logs.json()
    assert payload
    assert payload[0]["action"] == "project.created"


def test_source_guardian_unconfirmed_search_does_not_affect_auditor():
    with TestClient(app) as client:
        search = client.post("/api/source-guardian/search", json={"query": "华师 本科论文 规范"})

    assert search.status_code == 200
    payload = search.json()
    assert payload["status"] == "pending_user_confirmation"
    assert payload["sources"][0]["id"] == "manual-source-placeholder"
