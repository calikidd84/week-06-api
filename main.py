import json
import os
from typing import Any, Callable

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import func, inspect, or_, text
from sqlalchemy.orm import Session

from database import SessionLocal, engine, get_db
from models import Base, Book
from schemas import (
    AddBookToolInput,
    AgentRequest,
    ChatRequest,
    BookCreate,
    BookResponse,
    BookStatus,
    BookUpdate,
    DeleteBookToolInput,
    GetBookByIdToolInput,
    GetBooksToolInput,
    UpdateBookStatusToolInput,
    GetStatsToolInput,
    UpdateBookToolInput,
)
from seed import seed_books


load_dotenv()

Base.metadata.create_all(bind=engine)


def ensure_book_schema():
    inspector = inspect(engine)
    if not inspector.has_table("books"):
        return

    column_names = {column["name"] for column in inspector.get_columns("books")}
    statements = []
    if "genre" not in column_names:
        statements.append(
            "ALTER TABLE books ADD COLUMN genre VARCHAR(80) NOT NULL DEFAULT 'Fiction'"
        )
    if "description" not in column_names:
        statements.append(
            "ALTER TABLE books ADD COLUMN description TEXT NOT NULL DEFAULT ''"
        )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

app = FastAPI(title="Book Tracker API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^http://192\.168\.\d{1,3}\.\d{1,3}:3000$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_empty_database():
    ensure_book_schema()
    db = SessionLocal()
    try:
        if db.query(Book).count() == 0:
            seed_books()
    finally:
        db.close()


def get_api_token() -> str:
    token = os.environ.get("API_TOKEN") or os.environ.get("API_KEY")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="API_TOKEN (or API_KEY) is required for OpenRouter Models.",
        )
    return token


def get_ai_model_name() -> str:
    return os.environ.get("API_MODEL") or os.environ.get("MODEL_NAME") or "deepseek/deepseek-r1:free"


def get_ai_client():
    return OpenAI(
        base_url=os.environ.get("API_BASE_URL") or "https://openrouter.ai/api/v1",
        api_key=get_api_token(),
    )


def get_ai_messages(system_message: str, request: ChatRequest | AgentRequest):
    messages = [{"role": "system", "content": system_message}]

    for item in request.conversation_history:
        if isinstance(item, dict):
            if "role" in item and "content" in item:
                messages.append({"role": item["role"], "content": item["content"]})
            elif "user" in item:
                messages.append({"role": "user", "content": item["user"]})
            elif "assistant" in item:
                messages.append({"role": "assistant", "content": item["assistant"]})
            elif "content" in item:
                messages.append({"role": item.get("role", "user"), "content": item["content"]})
            else:
                messages.append({"role": "user", "content": json.dumps(item)})
        else:
            messages.append({"role": "user", "content": str(item)})

    messages.append({"role": "user", "content": request.message})
    return messages


@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Tracker API!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/books", response_model=list[BookResponse])
def get_books(
    status: str | None = None,
    genre: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if status:
        query = query.filter(Book.status == status)
    if genre:
        query = query.filter(func.lower(Book.genre) == genre.lower())
    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Book.title).like(pattern),
                func.lower(Book.author).like(pattern),
                func.lower(Book.genre).like(pattern),
                func.lower(Book.description).like(pattern),
            )
        )
    return query.order_by(Book.title).all()


@app.get("/books/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Book).count()
    want_to_read = db.query(Book).filter(Book.status == "want_to_read").count()
    reading = db.query(Book).filter(Book.status == "reading").count()
    read = db.query(Book).filter(Book.status == "read").count()
    average_rating = (
        db.query(Book)
        .filter(Book.status == "read")
        .with_entities(func.avg(Book.rating))
        .scalar()
        or 0
    )
    by_genre = (
        db.query(Book.genre, func.count(Book.id))
        .group_by(Book.genre)
        .order_by(Book.genre)
        .all()
    )
    return {
        "total": total,
        "want_to_read": want_to_read,
        "reading": reading,
        "read": read,
        "average_rating": round(float(average_rating), 2),
        "by_genre": {genre: count for genre, count in by_genre},
    }


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(data: BookCreate, db: Session = Depends(get_db)):
    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return Response(status_code=204)


@app.post("/ai/chat")
def chat_with_assistant(request: ChatRequest):
    messages = get_ai_messages(
        os.environ.get(
            "CONTEXT_PROMPT",
            "You are a helpful assistant. Answer the user's questions to the best of your ability.",
        ),
        request,
    )

    response = get_ai_client().chat.completions.create(
        model=get_ai_model_name(),
        messages=messages,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content

    return {
        "reply": reply,
        "updated_history": request.conversation_history
        + [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ],
    }


GENRE_ALIASES = {
    "science fiction": "sci-fi",
    "scifi": "sci-fi",
    "sci fi": "sci-fi",
    "sci-fi": "sci-fi",
    "comic": "comic books",
    "comics": "comic books",
    "comic book": "comic books",
    "comic books": "comic books",
    "manga": "manga",
    "fantasy": "fantasy",
    "fiction": "fiction",
    "nonfiction": "non-fiction",
    "non fiction": "non-fiction",
    "non-fiction": "non-fiction",
    "sports": "sports",
    "sport": "sports",
    "software": "software",
    "programming": "software",
    "coding": "software",
    "business": "business",
    "startup": "business",
    "how to": "how-to guides",
    "how-to": "how-to guides",
    "guide": "how-to guides",
    "guides": "how-to guides",
}

STOP_WORDS = {
    "about",
    "anything",
    "book",
    "books",
    "can",
    "find",
    "for",
    "give",
    "like",
    "me",
    "recommend",
    "recommendation",
    "recommendations",
    "show",
    "something",
    "that",
    "the",
    "want",
    "with",
}


def normalize_text(value: str):
    return value.lower().replace("-", " ")


def get_request_terms(message: str):
    normalized = normalize_text(message)
    return [
        word.strip(".,!?;:()[]{}\"'")
        for word in normalized.split()
        if len(word.strip(".,!?;:()[]{}\"'")) > 2
        and word.strip(".,!?;:()[]{}\"'") not in STOP_WORDS
    ]


def get_requested_genre(message: str):
    normalized = normalize_text(message)
    for alias, genre in sorted(GENRE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if normalize_text(alias) in normalized:
            return genre
    return None


def score_book(book: Book, terms: list[str], requested_genre: str | None):
    searchable = normalize_text(
        f"{book.title} {book.author} {book.genre} {book.description}"
    )
    score = 0
    if requested_genre and normalize_text(book.genre) == normalize_text(requested_genre):
        score += 20
    for term in terms:
        if term in searchable:
            score += 3
        if term in normalize_text(book.title):
            score += 4
        if term in normalize_text(book.genre):
            score += 5
    if book.rating:
        score += book.rating
    return score


def get_recommendation_candidates(db: Session, message: str, limit: int = 5):
    books = db.query(Book).all()
    requested_genre = get_requested_genre(message)
    terms = get_request_terms(message)

    scored_books = [
        (score_book(book, terms, requested_genre), book)
        for book in books
    ]
    matches = [
        book
        for score, book in sorted(
            scored_books,
            key=lambda item: (item[0], item[1].rating or 0, item[1].title),
            reverse=True,
        )
        if score > 0
    ]

    if matches:
        return matches[:limit]

    return (
        db.query(Book)
        .order_by(Book.rating.desc().nullslast(), Book.title)
        .limit(limit)
        .all()
    )


def build_recommendation_reply(candidates: list[Book], message: str):
    if not candidates:
        return "I could not find any books in the database yet. Try seeding the database first."

    intro = "Here are database-backed recommendations"
    requested_genre = get_requested_genre(message)
    if requested_genre:
        intro += f" for {requested_genre}"
    intro += ":"

    lines = [intro]
    for index, book in enumerate(candidates, start=1):
        rating = f", rating {book.rating}/5" if book.rating else ""
        lines.append(
            f"{index}. {book.title} by {book.author} "
            f"({book.genre}{rating}) - {book.description}"
        )
    return "\n".join(lines)


@app.post("/ai/recommend")
def recommend_books(request: ChatRequest, db: Session = Depends(get_db)):
    candidates = get_recommendation_candidates(db, request.message)
    reply = build_recommendation_reply(candidates, request.message)

    return {
        "reply": reply,
        "matches": [BookResponse.model_validate(book).model_dump() for book in candidates],
        "updated_history": request.conversation_history
        + [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ],
    }


BOOK_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_books",
            "description": (
                "Get the books in the user's library. Use this to inspect the collection, "
                "check current reading status, or find candidate books before updating or deleting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["want_to_read", "reading", "read"],
                        "description": "Optional status filter. Omit to return all books.",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_book_by_id",
            "description": "Fetch a single book by its database id. Use this after identifying the correct book.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Database id of the book.",
                    }
                },
                "required": ["book_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Get library statistics: total, counts by status, average rating, and by-genre counts.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_book",
            "description": "Add a new book to the user's library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Book title."},
                    "author": {"type": "string", "description": "Book author."},
                    "status": {
                        "type": "string",
                        "enum": ["want_to_read", "reading", "read"],
                        "description": "Reading status for the new book.",
                    },
                    "genre": {"type": "string", "description": "Optional genre label.", "default": "Fiction"},
                    "description": {"type": "string", "description": "Optional description.", "default": ""},
                    "rating": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Optional rating, only valid when status is read.",
                    },
                },
                "required": ["title", "author"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_book_status",
            "description": "Update a book's status and optional rating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Database id of the book to update.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["want_to_read", "reading", "read"],
                        "description": "New reading status.",
                    },
                    "rating": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Optional rating, only valid when status is read.",
                    },
                },
                "required": ["book_id", "status"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_book",
            "description": "Update any book fields (title, author, genre, description, status, rating).",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {"type": "integer", "description": "Database id of the book to update."},
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                    "genre": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["want_to_read", "reading", "read"]},
                    "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["book_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_book",
            "description": "Delete a book from the user's library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "integer",
                        "description": "Database id of the book to delete.",
                    }
                },
                "required": ["book_id"],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_INPUT_MODELS: dict[str, type[BaseModel]] = {
    "get_books": GetBooksToolInput,
    "get_book_by_id": GetBookByIdToolInput,
    "get_stats": GetStatsToolInput,
    "add_book": AddBookToolInput,
    "update_book_status": UpdateBookStatusToolInput,
    "delete_book": DeleteBookToolInput,
    "update_book": UpdateBookToolInput,
}


def serialize_book(book: Book) -> dict[str, Any]:
    return BookResponse.model_validate(book).model_dump()


def get_books_tool(db: Session, status: BookStatus | None = None):
    query = db.query(Book)
    if status:
        query = query.filter(Book.status == status)
    return [serialize_book(book) for book in query.order_by(Book.title).all()]


def get_stats_tool(db: Session):
    total = db.query(Book).count()
    want_to_read = db.query(Book).filter(Book.status == "want_to_read").count()
    reading = db.query(Book).filter(Book.status == "reading").count()
    read = db.query(Book).filter(Book.status == "read").count()
    average_rating = (
        db.query(Book)
        .filter(Book.status == "read")
        .with_entities(func.avg(Book.rating))
        .scalar()
        or 0
    )
    by_genre = (
        db.query(Book.genre, func.count(Book.id))
        .group_by(Book.genre)
        .order_by(Book.genre)
        .all()
    )
    return {
        "total": total,
        "want_to_read": want_to_read,
        "reading": reading,
        "read": read,
        "average_rating": round(float(average_rating), 2),
        "by_genre": {genre: count for genre, count in by_genre},
    }


def get_book_by_id_tool(db: Session, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return serialize_book(book)


def add_book_tool(
    db: Session,
    title: str,
    author: str,
    status: BookStatus = "want_to_read",
    genre: str = "Fiction",
    description: str = "",
    rating: int | None = None,
):
    payload = AddBookToolInput(
        title=title,
        author=author,
        status=status,
        genre=genre,
        description=description,
        rating=rating,
    ).model_dump()

    book = Book(**payload)
    db.add(book)
    db.commit()
    db.refresh(book)
    return serialize_book(book)


def update_book_status_tool(
    db: Session,
    book_id: int,
    status: BookStatus,
    rating: int | None = None,
):
    payload = UpdateBookStatusToolInput(
        book_id=book_id,
        status=status,
        rating=rating,
    ).model_dump()

    book = db.query(Book).filter(Book.id == payload["book_id"]).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.status = payload["status"]
    if payload["status"] == "read":
        if payload.get("rating") is not None:
            book.rating = payload["rating"]
    else:
        book.rating = None

    db.commit()
    db.refresh(book)
    return serialize_book(book)


def update_book_tool(
    db: Session,
    book_id: int,
    title: str | None = None,
    author: str | None = None,
    genre: str | None = None,
    description: str | None = None,
    status: BookStatus | None = None,
    rating: int | None = None,
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    updates = {
        k: v
        for k, v in {
            "title": title,
            "author": author,
            "genre": genre,
            "description": description,
            "status": status,
            "rating": rating,
        }.items()
        if v is not None
    }

    for key, value in updates.items():
        setattr(book, key, value)

    if updates.get("status") != "read":
        book.rating = None

    db.commit()
    db.refresh(book)
    return serialize_book(book)


def delete_book_tool(db: Session, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"deleted": True, "book_id": book_id}


def build_tool_functions(db: Session) -> dict[str, Callable[..., Any]]:
    return {
        "get_books": lambda **kwargs: get_books_tool(db, **kwargs),
        "get_book_by_id": lambda **kwargs: get_book_by_id_tool(db, **kwargs),
        "get_stats": lambda **kwargs: get_stats_tool(db, **kwargs),
        "add_book": lambda **kwargs: add_book_tool(db, **kwargs),
        "update_book_status": lambda **kwargs: update_book_status_tool(db, **kwargs),
        "update_book": lambda **kwargs: update_book_tool(db, **kwargs),
        "delete_book": lambda **kwargs: delete_book_tool(db, **kwargs),
    }


def validate_tool_input(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    model = TOOL_INPUT_MODELS[tool_name]
    return model.model_validate(tool_input).model_dump()


def normalize_conversation_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_history: list[dict[str, Any]] = []
    for item in history:
        role = item.get("role") if isinstance(item, dict) else None
        content = item.get("content") if isinstance(item, dict) else None
        if role and content is not None:
            normalized_history.append({"role": role, "content": content})
    return normalized_history


def serialize_assistant_message(message) -> dict[str, Any]:
    assistant_message: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
    }

    tool_calls = message.tool_calls or []
    if tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in tool_calls
        ]

    return assistant_message


def run_agent(request: AgentRequest, db: Session, max_iterations: int = 10):
    client = get_ai_client()
    tool_functions = build_tool_functions(db)
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a careful book tracker agent. Use the tools to inspect, add, update, "
                "and delete books. Never guess book ids. If the user asks for a change, find the "
                "right book first, then make the change. Keep the final answer concise and state "
                "exactly what you changed or found."
            ),
        },
        *normalize_conversation_history(request.conversation_history),
        {"role": "user", "content": request.message},
    ]
    agent_steps: list[dict[str, Any]] = []

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=get_ai_model_name(),
            messages=messages,
            tools=BOOK_AGENT_TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        choice = response.choices[0]
        messages.append(serialize_assistant_message(choice.message))

        tool_calls = choice.message.tool_calls or []
        if not tool_calls:
            final_text = choice.message.content or ""
            return final_text, agent_steps

        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                raw_tool_input = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                raw_tool_input = {}

            validated_tool_input = validate_tool_input(tool_name, raw_tool_input)
            result = tool_functions[tool_name](**validated_tool_input)
            agent_steps.append(
                {
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "input": validated_tool_input,
                    "result": result,
                }
            )
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        messages.extend(tool_messages)

    return "Agent stopped after reaching the max iteration limit.", agent_steps


@app.post("/ai/agent")
def book_agent(request: AgentRequest, db: Session = Depends(get_db)):
    response, agent_steps = run_agent(request, db)
    return {"response": response, "agent_steps": agent_steps}
