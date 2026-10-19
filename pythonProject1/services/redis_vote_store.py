from __future__ import annotations
import asyncio
from typing import Tuple
from services.redis_client import get_redis

# Lua scripts for atomic add/remove operations
LIKE_LUA = """
local added = redis.call('SADD', KEYS[1], ARGV[1])
if tonumber(added) == 1 then
  local new = redis.call('HINCRBY', KEYS[2], ARGV[2], 1)
  return {1, tostring(new)}
else
  local cur = redis.call('HGET', KEYS[2], ARGV[2]) or '0'
  return {0, cur}
end
"""

UNLIKE_LUA = """
local removed = redis.call('SREM', KEYS[1], ARGV[1])
if tonumber(removed) == 1 then
  local new = redis.call('HINCRBY', KEYS[2], ARGV[2], -1)
  if tonumber(new) < 0 then
    redis.call('HSET', KEYS[2], ARGV[2], 0)
    new = 0
  end
  return {1, tostring(new)}
else
  local cur = redis.call('HGET', KEYS[2], ARGV[2]) or '0'
  return {0, cur}
end
"""


def _message_key(chat_id: int, message_id: int) -> str:
    return f"message:{chat_id}:{message_id}"


def _likes_key(chat_id: int, message_id: int) -> str:
    return f"likes:{chat_id}:{message_id}"


def _super_likes_key(chat_id: int, message_id: int) -> str:
    return f"super_likes:{chat_id}:{message_id}"


async def _ensure_message_hash_exists(chat_id: int, message_id: int) -> None:
    r = get_redis()
    key = _message_key(chat_id, message_id)
    exists = await r.exists(key)
    if not exists:
        await r.hset(key, mapping={"like_count": "0", "super_like_count": "0"})


async def add_like(chat_id: int, message_id: int, user_id: int) -> Tuple[bool, int]:
    r = get_redis()
    await _ensure_message_hash_exists(chat_id, message_id)
    likes_key = _likes_key(chat_id, message_id)
    message_key = _message_key(chat_id, message_id)
    res = await r.eval(LIKE_LUA, 2, likes_key, message_key, str(user_id), "like_count")
    added = bool(int(res[0]))
    count = int(res[1])
    return added, count


async def add_super_like(chat_id: int, message_id: int, user_id: int) -> Tuple[bool, int]:
    r = get_redis()
    await _ensure_message_hash_exists(chat_id, message_id)
    s_key = _super_likes_key(chat_id, message_id)
    message_key = _message_key(chat_id, message_id)
    res = await r.eval(LIKE_LUA, 2, s_key, message_key, str(user_id), "super_like_count")
    added = bool(int(res[0]))
    count = int(res[1])
    return added, count


async def remove_like(chat_id: int, message_id: int, user_id: int) -> Tuple[bool, int]:
    r = get_redis()
    await _ensure_message_hash_exists(chat_id, message_id)
    likes_key = _likes_key(chat_id, message_id)
    message_key = _message_key(chat_id, message_id)
    res = await r.eval(UNLIKE_LUA, 2, likes_key, message_key, str(user_id), "like_count")
    removed = bool(int(res[0]))
    count = int(res[1])
    return removed, count


async def has_liked(chat_id: int, message_id: int, user_id: int) -> bool:
    r = get_redis()
    return await r.sismember(_likes_key(chat_id, message_id), str(user_id))


async def has_super_liked(chat_id: int, message_id: int, user_id: int) -> bool:
    r = get_redis()
    return await r.sismember(_super_likes_key(chat_id, message_id), str(user_id))


async def get_counts(chat_id: int, message_id: int) -> Tuple[int, int]:
    r = get_redis()
    key = _message_key(chat_id, message_id)
    data = await r.hgetall(key)
    like = int(data.get("like_count") or 0)
    super_like = int(data.get("super_like_count") or 0)
    return like, super_like
