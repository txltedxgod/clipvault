from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


snippet_tags = Table(
    'snippet_tags',
    Base.metadata,
    Column('snippet_id', Integer, ForeignKey('snippets.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
)


class Snippet(Base):
    __tablename__ = 'snippets'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    language = Column(String(50), default='text')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    tags = relationship('Tag', secondary=snippet_tags, back_populates='snippets')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'language': self.language,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': [t.name for t in self.tags],
        }


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    snippets = relationship('Snippet', secondary=snippet_tags, back_populates='tags')
