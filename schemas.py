from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


BookStatus = Literal["want_to_read", "reading", "read"]


class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    description: str = ""


class BookCreate(BookBase):
    status: BookStatus = "want_to_read"
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None

    @field_validator("rating")
    @classmethod
    def rating_only_for_read(cls, value, info):
        if value is not None and info.data.get("status") != "read":
            raise ValueError('rating is only allowed when status is "read"')
        return value


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BookStatus] = None
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None

    @field_validator("rating")
    @classmethod
    def rating_only_for_read(cls, value, info):
        if value is not None and info.data.get("status") != "read":
            raise ValueError('rating is only allowed when status is "read"')
        return value


class BookResponse(BookBase):
    id: int
    status: str
    rating: Optional[int]

    model_config = {"from_attributes": True}


class GetBooksToolInput(BaseModel):
    status: Optional[BookStatus] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in {"want_to_read", "want-to-read", "wanttoread"}:
                return "want_to_read"
            if normalized in {"reading", "read"}:
                return normalized
        return value


class GetBookByIdToolInput(BaseModel):
    book_id: int


class AddBookToolInput(BaseModel):
    title: str
    author: str
    status: BookStatus = "want_to_read"
    genre: str = "Fiction"
    description: str = ""
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in {"want_to_read", "want-to-read", "wanttoread"}:
                return "want_to_read"
            if normalized in {"reading", "read"}:
                return normalized
        return value

    @field_validator("rating")
    @classmethod
    def rating_only_for_read(cls, value, info):
        if value is not None and info.data.get("status") != "read":
            raise ValueError('rating is only allowed when status is "read"')
        return value


class UpdateBookStatusToolInput(BaseModel):
    book_id: int
    status: BookStatus
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in {"want_to_read", "want-to-read", "wanttoread"}:
                return "want_to_read"
            if normalized in {"reading", "read"}:
                return normalized
        return value

    @field_validator("rating")
    @classmethod
    def rating_only_for_read(cls, value, info):
        if value is not None and info.data.get("status") != "read":
            raise ValueError('rating is only allowed when status is "read"')
        return value


class DeleteBookToolInput(BaseModel):
    book_id: int


class UpdateBookToolInput(BaseModel):
    book_id: int
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BookStatus] = None
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in {"want_to_read", "want-to-read", "wanttoread"}:
                return "want_to_read"
            if normalized in {"reading", "read"}:
                return normalized
        return value

    @field_validator("rating")
    @classmethod
    def rating_only_for_read(cls, value, info):
        if value is not None and info.data.get("status") != "read":
            raise ValueError('rating is only allowed when status is "read"')
        return value


class GetStatsToolInput(BaseModel):
    pass


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)


class AgentRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
