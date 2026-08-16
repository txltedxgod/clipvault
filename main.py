from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from database import init_db, get_session
from models import Snippet, Tag, snippet_tags
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title='ClipVault', lifespan=lifespan)


class SnippetCreate(BaseModel):
    title: Optional[str] = None
    content: str
    language: str = 'text'
    tags: list[str] = []


class SnippetUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[list[str]] = None


async def get_or_create_tag(session: AsyncSession, name: str) -> Tag:
    result = await session.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=name)
        session.add(tag)
        await session.flush()
    return tag


@app.post('/api/snippets')
async def create_snippet(data: SnippetCreate, session: AsyncSession = Depends(get_session)):
    snippet = Snippet(
        title=data.title,
        content=data.content,
        language=data.language
    )
    for tag_name in data.tags:
        tag = await get_or_create_tag(session, tag_name.strip().lower())
        snippet.tags.append(tag)
    session.add(snippet)
    await session.commit()
    await session.refresh(snippet)
    return snippet.to_dict()


@app.get('/api/snippets')
async def list_snippets(
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    query = select(Snippet).options(selectinload(Snippet.tags))

    if q:
        query = query.where(
            or_(
                Snippet.title.ilike(f'%{q}%'),
                Snippet.content.ilike(f'%{q}%')
            )
        )
    if tag:
        query = query.join(snippet_tags).join(Tag).where(Tag.name == tag.lower())

    query = query.order_by(Snippet.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    snippets = result.scalars().unique().all()
    return [s.to_dict() for s in snippets]


@app.get('/api/snippets/{snippet_id}')
async def get_snippet(snippet_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Snippet).options(selectinload(Snippet.tags)).where(Snippet.id == snippet_id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')
    return snippet.to_dict()


@app.put('/api/snippets/{snippet_id}')
async def update_snippet(
    snippet_id: int,
    data: SnippetUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Snippet).options(selectinload(Snippet.tags)).where(Snippet.id == snippet_id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')

    if data.title is not None:
        snippet.title = data.title
    if data.content is not None:
        snippet.content = data.content
    if data.language is not None:
        snippet.language = data.language
    if data.tags is not None:
        snippet.tags.clear()
        for tag_name in data.tags:
            tag = await get_or_create_tag(session, tag_name.strip().lower())
            snippet.tags.append(tag)

    await session.commit()
    await session.refresh(snippet)
    return snippet.to_dict()


@app.delete('/api/snippets/{snippet_id}')
async def delete_snippet(snippet_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Snippet).where(Snippet.id == snippet_id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail='not found')
    await session.delete(snippet)
    await session.commit()
    return {'ok': True}


@app.get('/api/tags')
async def list_tags(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [{'id': t.id, 'name': t.name} for t in tags]
