from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate

from app.agent.llm import FindingAnalysis
from app.agent.prompts import ANALYZE_PROMPT


@dataclass
class AnalysisUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class AnalysisResult:
    finding: FindingAnalysis
    usage: AnalysisUsage


class AnalysisService:

    def __init__(self, model):
        self.model = model

        self.prompt = ChatPromptTemplate.from_template(
            ANALYZE_PROMPT
        )

        self.chain = (
            self.prompt
            | self.model.with_structured_output(
                FindingAnalysis,
                include_raw=True,
            )
        )

    async def analyze(
        self,
        evidence: str,
    ) -> AnalysisResult:

        response = await self.chain.ainvoke(
            {
                "evidence": evidence,
            }
        )

        parsed = response["parsed"]
        raw = response["raw"]

        usage_metadata = getattr(
            raw,
            "usage_metadata",
            None,
        )

        if usage_metadata is None:
            usage = AnalysisUsage()
        else:
            input_tokens = int(
                usage_metadata.get(
                    "input_tokens",
                    0,
                )
                or 0
            )

            output_tokens = int(
                usage_metadata.get(
                    "output_tokens",
                    0,
                )
                or 0
            )

            total_tokens = int(
                usage_metadata.get(
                    "total_tokens",
                    input_tokens + output_tokens,
                )
                or 0
            )

            usage = AnalysisUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

        return AnalysisResult(
            finding=parsed,
            usage=usage,
        )