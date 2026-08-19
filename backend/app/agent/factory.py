from app.agent.executor import WorkflowExecutor
from app.agent.llm_service import AnalysisService
from app.agent.model import create_analysis_model
from app.agent.stage_handlers import StageHandler


def create_workflow_executor() -> WorkflowExecutor:
    analysis_service = AnalysisService(
        model=create_analysis_model(),
    )

    handler = StageHandler(
        analysis_service=analysis_service,
    )

    return WorkflowExecutor(
        handler=handler,
    )