import pytest
from telegram_rutor_bot.db.models import Film, Torrent, Search, User, Category
from telegram_rutor_bot.schemas import TorrentResponse, FilmResponse, UserResponse
from datetime import datetime, UTC

def test_models_init():
    # Just instantiate to cover init and repr
    f = Film(name="Test", year=2024)
    assert f.name == "Test"
    
    t = Torrent(name="Tor", magnet="mag")
    assert t.name == "Tor"
    
    s = Search(query="Query")
    assert s.query == "Query"
    
    u = User(chat_id=123)
    assert u.chat_id == 123
    
    c = Category(name="Cat")
    assert c.name == "Cat"

def test_schemas_validate():
    # Test Pydantic models
    # Correcting with all required fields
    tr = TorrentResponse(
        id=1, 
        name="Test", 
        magnet="mag", 
        size=100, 
        created_at=datetime.now(UTC), 
        blake="123", 
        film_id=1,
        created=datetime.now(UTC).date(),
        link="/torrent/123",
        sz=100,
        approved=True,
        downloaded=False,
        seeds=10,
        date="2024-01-01"
    )
    assert tr.name == "Test"
