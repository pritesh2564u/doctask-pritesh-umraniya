import pytest

from app.agent.llm import FindingAnalysis
from app.agent.llm_service import AnalysisService
from app.agent.model import create_analysis_model


@pytest.mark.asyncio
async def test_groq_returns_structured_analysis():
    model = create_analysis_model()

    service = AnalysisService(
        model=model,
    )

    result = await service.analyze(
        """
        The payment integration is delayed by two weeks.
        The team is blocked waiting for the required API
        credentials, putting the release at risk.
        """
    )

    assert isinstance(
        result,
        FindingAnalysis,
    )

    assert isinstance(
        result.is_risk,
        bool,
    )

    assert result.title.strip()
    assert result.description.strip()

    assert result.is_risk is True