"""Response models for the web API (these also power the docs at /docs)."""
from pydantic import BaseModel


class TopicSummary(BaseModel):
    index: int
    post_id: str
    subreddit: str | None
    title: str
    url: str | None
    score: int | None
    comment_count: int
    entities: list[str]
    mode: str  # "entity" or "topic"


class StanceCount(BaseModel):
    label: str
    count: int
    pct: float


class Reason(BaseModel):
    label: str
    keywords: list[str]
    examples: list[str]


class TopicReport(BaseModel):
    index: int
    post_id: str
    title: str
    subreddit: str | None
    url: str | None
    mode: str
    entities: list[str]
    min_len: int
    total: int
    distribution: list[StanceCount]
    reasons: list[Reason]


class RefreshStatus(BaseModel):
    running: bool
    step: int
    total_steps: int
    label: str
    error: str | None
    finished_at: int | None
