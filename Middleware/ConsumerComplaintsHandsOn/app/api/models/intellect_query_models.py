from pydantic import BaseModel, ConfigDict, Field


class IntellectQueryBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    limit: int = Field(default=5, ge=1, le=50)
    config: str = Field(default="baseline", min_length=1, max_length=32)


class IntellectHitOut(BaseModel):
    id: str
    text: str
    score: float


class IntellectQueryOut(BaseModel):
    hits: list[IntellectHitOut]
    config: str = "baseline"
