from langchain_core.prompts import ChatPromptTemplate

from app.agent.llm import FindingAnalysis
from app.agent.prompts import ANALYZE_PROMPT


class AnalysisService:

    def __init__(self, model):
        self.model = model

        self.prompt = ChatPromptTemplate.from_template(
            ANALYZE_PROMPT
        )

        self.chain = (
            self.prompt
            | self.model.with_structured_output(
                FindingAnalysis
            )
        )

    async def analyze(
        self,
        evidence: str,
    ) -> FindingAnalysis:

        return await self.chain.ainvoke(
            {
                "evidence": evidence,
            }
        )