import pytest
from httpx  import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
class TestHealth:

    async def test_health_returns_200(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.status_code == 200

    async def test_health_status_healthy(self, client: AsyncClient):
        data = (await client.get("/health")).json()
        assert data["status"] == "healthy"

    async def test_root_returns_system_info(self, client: AsyncClient):
        data = (await client.get("/")).json()
        assert data["system"] == "THEMIS"
        assert "EvidenceChain™" in data["differentiators"]


@pytest.mark.asyncio
class TestAnalyzeEndpoint:

    async def test_rejects_non_pdf(self, client: AsyncClient):
        r = await client.post("/analyze",
            files={"file": ("test.txt", b"content", "text/plain")},
            data={"system_name": "Test"})
        assert r.status_code == 400

    async def test_accepts_pdf_returns_session_id(self, client: AsyncClient, sample_pdf: Path):
        r = await client.post("/analyze",
            files={"file": ("doc.pdf", sample_pdf.read_bytes(), "application/pdf")},
            data={"system_name": "TestAI", "frameworks": "eu_ai_act"})
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert data["session_id"].startswith("TMS-")
        assert data["status"] == "pending"

    async def test_session_id_format(self, client: AsyncClient, sample_pdf: Path):
        r    = await client.post("/analyze",
            files={"file": ("doc.pdf", sample_pdf.read_bytes(), "application/pdf")},
            data={"system_name": "TestAI"})
        data = r.json()
        sid  = data["session_id"]
        parts = sid.split("-")
        assert parts[0] == "TMS"
        assert len(parts[1]) == 6


@pytest.mark.asyncio
class TestSessionEndpoint:

    async def test_unknown_session_returns_404(self, client: AsyncClient):
        r = await client.get("/sessions/TMS-UNKNOWN")
        assert r.status_code == 404

    async def test_known_session_returns_status(self, client: AsyncClient, sample_pdf: Path):
        r1  = await client.post("/analyze",
            files={"file": ("doc.pdf", sample_pdf.read_bytes(), "application/pdf")},
            data={"system_name": "TestAI"})
        sid = r1.json()["session_id"]
        r2  = await client.get(f"/sessions/{sid}")
        assert r2.status_code == 200
        data = r2.json()
        assert "status" in data
        assert data["status"] in ["pending", "running", "completed", "error"]

    async def test_report_returns_202_while_running(self, client: AsyncClient, sample_pdf: Path):
        r1  = await client.post("/analyze",
            files={"file": ("doc.pdf", sample_pdf.read_bytes(), "application/pdf")},
            data={"system_name": "TestAI"})
        sid = r1.json()["session_id"]
        r2  = await client.get(f"/sessions/{sid}/report")
        # While still pending/running, should return 202
        assert r2.status_code in [200, 202]
