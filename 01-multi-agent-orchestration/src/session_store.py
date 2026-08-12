import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from .models import BrandAnalysis

dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("SESSION_TABLE", "AGENTICOPS-sessions-01")
table = dynamodb.Table(table_name)


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
        table.put_item(Item=item)
        return item

    @staticmethod
    def append_event(session_id: str, event: dict):
        table.update_item(
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
        response = table.get_item(Key={"session_id": session_id})
        return response.get("Item")

    @staticmethod
    def save_analysis(session_id: str, analysis: BrandAnalysis):
        table.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET analysis = :analysis, #st = :status, updated_at = :now",
            ExpressionAttributeNames={"#st": "state"},
            ExpressionAttributeValues={
                ":analysis": analysis.model_dump(),
                ":status": "completed",
                ":now": datetime.utcnow().isoformat(),
            },
        )
