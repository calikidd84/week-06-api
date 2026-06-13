from sqlalchemy import Column, Integer, String, Text

from database import Base


class Book(Base):
	__tablename__ = "books"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(200), nullable=False, index=True)
	author = Column(String(160), nullable=False, index=True)
	genre = Column(String(80), nullable=False, index=True)
	status = Column(String(30), nullable=False, default="want_to_read", index=True)
	rating = Column(Integer, nullable=True)
	description = Column(Text, nullable=False, default="")


__all__ = ["Base", "Book"]
