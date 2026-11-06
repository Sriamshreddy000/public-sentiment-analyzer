"""Response models for the web API (these also power the docs at /docs)."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TopicSummary(BaseModel):
    index: int
    post_id: str
    subreddit: str | None
    title: str
    url: str | None
    score: int | None
    num_comments: int | None   # total on Reddit (Arctic Shift snapshot)
    comment_count: int         # fetched (and labeled)
    fetch_error: str | None    # why no comments were fetched, if none were
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
    num_comments: int | None
    comment_count: int         # fetched
    excluded: int              # fetched but too short to use
    fetch_error: str | None
    mode: str
    entities: list[str]
    min_len: int
    total: int
    distribution: list[StanceCount]
    reasons: list[Reason]


class RefreshOptions(BaseModel):
    posts: int = Field(15, ge=1, le=50, description="How many topics to fetch and analyze")
    sort: Literal["trending", "newest"] = "trending"
    comments: Literal["all"] | Annotated[int, Field(ge=5, le=5000)] = Field(
        30, description='Comments analyzed per topic, or "all"')
    comment_order: Literal["top", "newest"] = Field(
        "top", description="Which comments to keep when capped")


class DataSummary(BaseModel):
    topics: int
    comments: int
    fetched_utc: int | None
    options: RefreshOptions | None  # settings used, if the data came from a website refresh


class RefreshStatus(BaseModel):
    running: bool
    step: int
    total_steps: int
    label: str
    detail: str
    error: str | None
    finished_at: int | None
    options: RefreshOptions | None = None
