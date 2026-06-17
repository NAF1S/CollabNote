import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
KAFKA_TOPIC = "collabnote_events"

kafka_producer: Optional[AIOKafkaProducer] = None


async def init_kafka_producer():
    """Initialize Kafka producer."""
    global kafka_producer
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await kafka_producer.start()
        print(f"Kafka Producer started. Brokers: {KAFKA_BROKERS}, Topic: {KAFKA_TOPIC}")
    except Exception as e:
        print(f"Failed to initialize Kafka producer: {e}")


async def close_kafka_producer():
    """Close Kafka producer."""
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()
        print("Kafka Producer stopped")


async def publish_event(
    event_type: str,
    user_id: int,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish an event to Kafka (fire-and-forget).
    
    Args:
        event_type: Type of event (user_signup, user_login, note_created, etc.)
        user_id: ID of the user performing the action
        resource_id: ID of the affected resource (note ID, etc.) - optional
        metadata: Additional metadata for the event
    
    Returns:
        True if published successfully, False otherwise
    """
    if not kafka_producer:
        print("Kafka producer not initialized")
        return False
    
    try:
        event_payload = {
            "event_type": event_type,
            "user_id": user_id,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        }
        
        # Fire-and-forget: don't await the send
        kafka_producer.send_and_forget(
            KAFKA_TOPIC,
            value=event_payload
        )
        
        print(f"Event published: {event_type} for user {user_id}")
        return True
    except Exception as e:
        print(f"Failed to publish event: {e}")
        return False
