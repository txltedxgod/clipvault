from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_session, init_db
from models import Snippet, Tag, snippet_tags

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title='ClipVault', lifespan=lifespan)
if STATIC_DIR.is_dir():
    app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


class SnippetCreate(BaseModel):
    title: str | None = None
    content: str
    language: str = 'text'
    tags: list[str] = []

    @field_validator('content')
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('content must not be blank')
        return value


class SnippetUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    language: str | None = None
    tags: list[str] | None = None

    @field_validator('content')
    @classmethod
    def content_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError('content must not be blank')
        return value


def _normalize_tags(raw_tags: list[str]) -> list[str]:
    return list(dict.fromkeys(t.strip().lower() for t in raw_tags if t and t.strip()))


def _escape_like(term: str) -> str:
    return term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


async def _get_snippet_with_tags(session: AsyncSession, snippet_id: int) -> Snippet | None:
    result = await session.execute(
        select(Snippet).options(selectinload(Snippet.tags)).where(Snippet.id == snippet_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_tag(session: AsyncSession, name: str) -> Tag:
    result = await session.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=name)
        session.add(tag)
        await session.flush()
    return tag


@app.get('/', include_in_schema=False)
async def serve_index():
    return FileResponse(STATIC_DIR / 'index.html')


@app.get('/health')
async def health_check():
    return {'status': 'ok'}


@app.post('/api/snippets')
async def create_snippet(data: SnippetCreate, session: SessionDep):
    snippet = Snippet(
        title=data.title.strip() if data.title and data.title.strip() else None,
        content=data.content,
        language=data.language.strip() or 'text',
    )
    for tag_name in _normalize_tags(data.tags):
        tag = await get_or_create_tag(session, tag_name)
        snippet.tags.append(tag)
    session.add(snippet)
    await session.commit()
    reloaded = await _get_snippet_with_tags(session, snippet.id)
    return reloaded.to_dict()


@app.get('/api/snippets')
async def list_snippets(
    session: SessionDep,
    q: str | None = Query(None),
    tag: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(Snippet).options(selectinload(Snippet.tags))

    if q and q.strip():
        escaped = _escape_like(q.strip())
        query = query.where(
            or_(
                Snippet.title.ilike(f'%{escaped}%', escape='\\'),
                Snippet.content.ilike(f'%{escaped}%', escape='\\'),
            )
        )
    if tag and tag.strip():
        query = query.join(snippet_tags).join(Tag).where(Tag.name == tag.strip().lower())

    query = query.order_by(Snippet.created_at.desc(), Snippet.id.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    snippets = result.scalars().unique().all()
    return [s.to_dict() for s in snippets]


@app.get('/api/snippets/{snippet_id}')
async def get_snippet(snippet_id: int, session: SessionDep):
    snippet = await _get_snippet_with_tags(session, snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')
    return snippet.to_dict()


@app.put('/api/snippets/{snippet_id}')
async def update_snippet(
    snippet_id: int,
    data: SnippetUpdate,
    session: SessionDep,
):
    snippet = await _get_snippet_with_tags(session, snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')

    if data.title is not None:
        snippet.title = data.title.strip() or None
    if data.content is not None:
        snippet.content = data.content
    if data.language is not None:
        snippet.language = data.language.strip() or 'text'
    if data.tags is not None:
        snippet.tags.clear()
        for tag_name in _normalize_tags(data.tags):
            tag = await get_or_create_tag(session, tag_name)
            snippet.tags.append(tag)

    await session.commit()
    reloaded = await _get_snippet_with_tags(session, snippet.id)
    return reloaded.to_dict()


@app.delete('/api/snippets/{snippet_id}')
async def delete_snippet(snippet_id: int, session: SessionDep):
    result = await session.execute(select(Snippet).where(Snippet.id == snippet_id))
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')
    await session.delete(snippet)
    await session.commit()
    return {'ok': True}


@app.get('/api/tags')
async def list_tags(session: SessionDep):
    result = await session.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [{'id': t.id, 'name': t.name} for t in tags]
