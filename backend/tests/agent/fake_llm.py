from typing import Any

from langchain_core.runnables import Runnable

from app.agent.llm import FindingAnalysis


class FakeAnalysisModel(Runnable):
    def with_structured_output(
        self,
        schema: type[FindingAnalysis],
    ):
        return self

    def invoke(
        self,
        input: Any,
        config: dict | None = None,
        **kwargs: Any,
    ) -> FindingAnalysis:
        evidence = self._extract_evidence(input)
        return self._analyze(evidence)

    async def ainvoke(
        self,
        input: Any,
        config: dict | None = None,
        **kwargs: Any,
    ) -> FindingAnalysis:
        evidence = self._extract_evidence(input)
        return self._analyze(evidence)

    @staticmethod
    def _extract_evidence(input: Any) -> str:
        # Direct dictionary input.
        if isinstance(input, dict):
            return str(input.get("evidence", ""))

        # LangChain PromptValue.
        if hasattr(input, "to_messages"):
            messages = input.to_messages()

            if messages:
                content = messages[-1].content

                if isinstance(content, str):
                    marker = "Evidence:"

                    if marker in content:
                        return content.split(
                            marker,
                            1,
                        )[1].strip()

                    return content

        return str(input)

    @staticmethod
    def _analyze(
        evidence: str,
    ) -> FindingAnalysis:

        text = evidence.lower()

        if any(
            keyword in text
            for keyword in [
                "risk",
                "delay",
                "delayed",
                "blocked",
                "overdue",
                "critical",
            ]
        ):
            return FindingAnalysis(
                is_risk=True,
                title="Potential delivery risk",
                description=evidence,
            )

        return FindingAnalysis(
            is_risk=False,
            title="No delivery risk",
            description=evidence,
        )