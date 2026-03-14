import pytest, asyncio
from httpx     import AsyncClient, ASGITransport
from api.main  import app
from core.state import initial_state
from core.models import Framework


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
def sample_state():
    return initial_state(
        session_id="TMS-TEST01",
        system_name="TestAI v1",
        system_text="This AI system makes automated credit decisions. "
                    "It processes personal financial data. No human oversight "
                    "is currently implemented. Transparency documentation missing.",
        frameworks=[Framework.EU_AI_ACT, Framework.GDPR],
    )


@pytest.fixture
def sample_pdf(tmp_path):
    # Create a minimal PDF for upload tests
    pdf = tmp_path / "test_system.pdf"
    pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj\n< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    )
    return pdf
