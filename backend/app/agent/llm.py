from pydantic import BaseModel, Field


class FindingAnalysis(BaseModel):
    is_risk: bool = Field(
        description=(
            "Whether the evidence indicates a meaningful "
            "delivery risk."
        )
    )

    title: str = Field(
        description="Short title for the identified finding."
    )

    description: str = Field(
        description=(
            "Clear description of the finding based only "
            "on the evidence."
        )
    )