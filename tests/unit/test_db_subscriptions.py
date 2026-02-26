import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_rutor_bot.db.subscriptions import (
    subscribe,
    unsubscribe,
    get_subscriptions,
    is_subscribed
)
from telegram_rutor_bot.db.models import User, Search

@pytest.mark.asyncio
async def test_subscription_lifecycle(async_session: AsyncSession):
    # Setup user and search
    user = User(chat_id=123, is_authorized=True)
    search = Search(url="http://test", cron="* * * * *")
    async_session.add_all([user, search])
    await async_session.commit()
    await async_session.refresh(user)
    await async_session.refresh(search)
    
    # Subscribe
    success, msg = await subscribe(async_session, search.id, user.chat_id)
    assert success is True
    assert msg == "Subscribed successfully"
    
    # Check if subscribed
    assert await is_subscribed(async_session, search.id, user.id) is True
    
    # Already subscribed
    success, msg = await subscribe(async_session, search.id, user.chat_id)
    assert success is False
    assert msg == "Already subscribed"
    
    # Get subscriptions
    subs = await get_subscriptions(async_session, user.id)
    assert len(subs) == 1
    assert subs[0].id == search.id
    
    # Unsubscribe
    un_success = await unsubscribe(async_session, search.id, user.id)
    assert un_success is True
    assert await is_subscribed(async_session, search.id, user.id) is False

@pytest.mark.asyncio
async def test_subscribe_user_not_found(async_session: AsyncSession):
    success, msg = await subscribe(async_session, 1, 999)
    assert success is False
    assert "User with chat_id 999 not found" in msg

@pytest.mark.asyncio
async def test_subscribe_search_not_found(async_session: AsyncSession):
    user = User(chat_id=555)
    async_session.add(user)
    await async_session.commit()
    
    success, msg = await subscribe(async_session, 9999, 555)
    assert success is False
    assert "Search with id 9999 not found" in msg
