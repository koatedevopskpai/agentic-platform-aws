import boto3
import json
import os
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Optional
from .models import BrandAnalysis

table_name = os.getenv("SESSION_TABLE", "AGENTICOPS-sessions-01")


@lru_cache(maxsize=None)
def _table():
    """Created on first use so importing this module needs no AWS region or credentials."""
    return boto3.resource("dynamodb").Table(table_name)


class SessionStore:
    TTL_HOURS = 1

    @staticmethod
    def create_session(client_id: str) -> dict:
        session_id = f"sess_{client_id}_{int(datetime.utcnow().timestamp())}"
        item = {
            "session_id": session_id,
            "client_id": client_id,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int(
                (datetime.utcnow() + timedelta(hours=SessionStore.TTL_HOURS)).timestamp()
            ),
            "state": "active",
            "events": [],
        }
        _table().put_item(Item=item)
        return item

    @staticmethod
    def append_event(session_id: str, event: dict):
        _table().update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET #evts = list_append(if_not_exists(#evts, :empty), :event)",
            ExpressionAttributeNames={"#evts": "events"},
            ExpressionAttributeValues={
                ":event": [event],
                ":empty": [],
            },
        )

    @staticmethod
    def get_session(session_id: str) -> Optional[dict]:
        response = _table().get_item(Key={"session_id": session_id})
        return response.get("Item")

    @staticmethod
    def save_analysis(session_id: str, analysis: BrandAnalysis):
        _table().update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET analysis = :analysis, #st = :status, updated_at = :now",
            ExpressionAttributeNames={"#st": "state"},
            ExpressionAttributeValues={
                ":analysis": analysis.model_dump(),
                ":status": "completed",
                ":now": datetime.utcnow().isoformat(),
            },
        )
