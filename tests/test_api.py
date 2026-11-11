import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import get_session
from main import app
from models import Base


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / 'test_clipvault.db'
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}', echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_serves_frontend_and_health(client):
    assert client.get('/health').json() == {'status': 'ok'}

    index_res = client.get('/')
    assert index_res.status_code == 200
    assert 'ClipVault' in index_res.text

    js_res = client.get('/static/app.js')
    assert js_res.status_code == 200
    assert 'createElement' in js_res.text


def test_snippet_crud_tag_normalization_and_validation(client):
    blank = client.post('/api/snippets', json={'title': 'bad', 'content': '   '})
    assert blank.status_code == 422

    created = client.post(
        '/api/snippets',
        json={
            'title': '  QuickSort  ',
            'content': 'def qsort(xs): return xs',
            'language': 'python',
            'tags': [' Python ', 'python', '', 'Algorithms'],
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body['title'] == 'QuickSort'
    assert body['tags'] == ['python', 'algorithms']

    snippet_id = body['id']
    fetched = client.get(f'/api/snippets/{snippet_id}')
    assert fetched.status_code == 200
    assert fetched.json()['content'] == 'def qsort(xs): return xs'

    updated = client.put(
        f'/api/snippets/{snippet_id}',
        json={'title': 'Updated', 'tags': ['FastAPI', ' fastapi ']},
    )
    assert updated.status_code == 200
    assert updated.json()['title'] == 'Updated'
    assert updated.json()['tags'] == ['fastapi']

    tags = client.get('/api/tags').json()
    assert [t['name'] for t in tags] == ['algorithms', 'fastapi', 'python']

    deleted = client.delete(f'/api/snippets/{snippet_id}')
    assert deleted.status_code == 200
    assert deleted.json() == {'ok': True}
    assert client.get(f'/api/snippets/{snippet_id}').status_code == 404


def test_search_like_escaping_and_tag_filtering(client):
    client.post(
        '/api/snippets',
        json={'title': '100% Real', 'content': 'select 1', 'language': 'sql', 'tags': ['db']},
    )
    client.post(
        '/api/snippets',
        json={'title': 'Plain', 'content': 'echo hi', 'language': 'bash', 'tags': ['shell']},
    )

    pct_match = client.get('/api/snippets', params={'q': '100%'}).json()
    assert len(pct_match) == 1
    assert pct_match[0]['title'] == '100% Real'

    tag_match = client.get('/api/snippets', params={'tag': 'SHELL'}).json()
    assert len(tag_match) == 1
    assert tag_match[0]['title'] == 'Plain'
