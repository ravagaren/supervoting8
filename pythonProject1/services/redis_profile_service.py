from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from services.redis_client import get_redis


class RedisProfileService:
    """Redis-backed user profile service.

    Keys used:
      - profile:{user_id} -> HASH with fields (nickname, age, city, position, created_at, ...)
      - profiles -> SET of user_id
    """

    def __init__(self):
        self._r = get_redis()

    async def save_profile(self, profile: Any) -> None:
        """Persist profile to Redis.

        Accepts either a dataclass-like object or a mapping.
        """
        # Normalize to mapping
        if is_dataclass(profile):
            mapping = asdict(profile)
        elif isinstance(profile, dict):
            mapping = dict(profile)
        else:
            mapping = {k: getattr(profile, k) for k in ("user_id", "nickname", "age", "city", "position") if hasattr(profile, k)}

        user_id = int(mapping.get("user_id"))
        key = f"profile:{user_id}"

        # Ensure values are strings for HSET
        text_map: Dict[str, str] = {}
        for k, v in mapping.items():
            if v is None:
                continue
            if isinstance(v, (dict, list)):
                text_map[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, datetime):
                text_map[k] = v.isoformat()
            else:
                text_map[k] = str(v)

        if "created_at" not in text_map:
            text_map["created_at"] = datetime.utcnow().isoformat()

        await self._r.hset(key, mapping=text_map)
        await self._r.sadd("profiles", str(user_id))

    async def exists(self, user_id: int) -> bool:
        key = f"profile:{user_id}"
        v = await self._r.exists(key)
        return bool(v)

    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        key = f"profile:{user_id}"
        data = await self._r.hgetall(key)
        if not data:
            return None
        # Try to decode JSON fields
        for k, v in list(data.items()):
            if v is None:
                continue
            if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
                try:
                    data[k] = json.loads(v)
                except Exception:
                    pass
        # parse created_at
        if "created_at" in data:
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"])  # type: ignore[arg-type]
            except Exception:
                pass
        return data

    async def load_all_profiles(self) -> Dict[int, Dict[str, Any]]:
        members = await self._r.smembers("profiles")
        out: Dict[int, Dict[str, Any]] = {}
        for uid in members:
            try:
                uid_i = int(uid)
            except Exception:
                continue
            profile = await self.get_profile(uid_i)
            if profile is not None:
                out[uid_i] = profile
        return out


# module-level instance
redis_profile_service = RedisProfileService()
