import asyncio
import json
import os
import signal
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv
from mongodb import MongoDBManager

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
KAFKA_TOPIC = "collabnote_events"
KAFKA_GROUP_ID = "activity-logger-group"


class KafkaActivityConsumer:
    """Consume events from Kafka and write to MongoDB activity_logs."""
    
    def __init__(self):
        self.consumer = None
        self.db_manager = MongoDBManager()
        self.running = True
    
    async def start(self):
        """Start the Kafka consumer."""
        try:
            # Connect to MongoDB
            await self.db_manager.connect()
            
            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKERS,
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                session_timeout_ms=30000,
            )
            
            await self.consumer.start()
            print(f"Consumer started. Listening to topic: {KAFKA_TOPIC}")
            print(f"Brokers: {KAFKA_BROKERS}")
            print(f"Group ID: {KAFKA_GROUP_ID}")
            
            # Start consuming messages
            await self._consume_messages()
        
        except Exception as e:
            print(f"Error starting consumer: {e}")
        finally:
            await self.stop()
    
    async def _consume_messages(self):
        """Consume messages from Kafka and write to MongoDB."""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                event = message.value
                print(f"Received event: {event}")
                
                # Add MongoDB _id automatically
                await self.db_manager.insert_activity_log(event)
        
        except asyncio.CancelledError:
            print("Consumer task cancelled")
        except Exception as e:
            print(f"Error consuming messages: {e}")
    
    async def stop(self):
        """Stop the consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            print("Consumer stopped")
        
        await self.db_manager.disconnect()


async def main():
    """Main entry point."""
    consumer = KafkaActivityConsumer()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutdown signal received")
        asyncio.create_task(consumer.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await consumer.start()


if __name__ == "__main__":
    print("Starting Activity Logger Consumer...")
    asyncio.run(main())
