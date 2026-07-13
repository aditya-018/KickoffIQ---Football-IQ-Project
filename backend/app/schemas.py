from typing import Literal

from pydantic import BaseModel, Field


ScenarioType = Literal["offside", "penalty", "throw_in", "general"]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class Source(BaseModel):
    title: str
    detail: str
    url: str | None = None
    score: float | None = None


class Diagram(BaseModel):
    scenario_type: ScenarioType
    title: str
    svg: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    diagram: Diagram | None = None
