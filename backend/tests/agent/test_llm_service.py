import pytest

from app.agent.llm import FindingAnalysis
from app.agent.llm_service import AnalysisService
from tests.agent.fake_llm import FakeAnalysisModel


@pytest.mark.asyncio
async def test_analysis_service_returns_structured_risk():
    service = AnalysisService(
        model=FakeAnalysisModel()
    )

    result = await service.analyze(
        "The project is delayed and currently at risk."
    )

    assert isinstance(
        result,
        FindingAnalysis,
    )

    assert result.is_risk is True

    assert result.title == "Potential delivery risk"

    assert (
        "delayed"
        in result.description.lower()
    )


@pytest.mark.asyncio
async def test_analysis_service_returns_non_risk():
    service = AnalysisService(
        model=FakeAnalysisModel()
    )

    result = await service.analyze(
        "The project was completed successfully."
    )

    assert isinstance(
        result,
        FindingAnalysis,
    )

    assert result.is_risk is False