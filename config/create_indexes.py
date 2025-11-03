#!/usr/bin/env python3
"""
Create payload indexes for the WillGPT Qdrant collection to enable filtering
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
from dotenv import load_dotenv


load_dotenv()

# Configuration
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is required")

QDRANT_URL = os.getenv("QDRANT_URL")
if not QDRANT_URL:
    raise ValueError("QDRANT_URL environment variable is required")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "will-gpt")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-m3")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 4))


def create_indexes():
    """Create indexes for common filter fields"""
    
    print("Connecting to Qdrant...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60,
        prefer_grpc=False,
    )
    
    print(f"\nCreating indexes for collection: {COLLECTION_NAME}\n")
    
    # Index for platform field (keyword)
    print("Creating index for 'platform' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="platform",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✓ 'platform' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'platform' index: {e}")
    
    # Index for has_interpretations field (bool)
    print("\nCreating index for 'has_interpretations' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="has_interpretations",
            field_schema=PayloadSchemaType.BOOL,
        )
        print("✓ 'has_interpretations' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'has_interpretations' index: {e}")
    
    # Index for timestamp field (float/integer)
    print("\nCreating index for 'timestamp' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="timestamp",
            field_schema=PayloadSchemaType.FLOAT,
        )
        print("✓ 'timestamp' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'timestamp' index: {e}")
    
    # Index for conversation_title field (text/keyword)
    print("\nCreating index for 'conversation_title' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="conversation_title",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✓ 'conversation_title' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'conversation_title' index: {e}")

    # Index for conversation_id field (keyword) - REQUIRED FOR GROUPING
    print("\nCreating index for 'conversation_id' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="conversation_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✓ 'conversation_id' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'conversation_id' index: {e}")

    # Index for assistant_model field (keyword) - REQUIRED FOR GROUPING
    print("\nCreating index for 'assistant_model' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="assistant_model",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✓ 'assistant_model' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'assistant_model' index: {e}")

    # Index for turn_number field (integer) - REQUIRED FOR ORDER_BY
    print("\nCreating index for 'turn_number' field...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="turn_number",
            field_schema=PayloadSchemaType.INTEGER,
        )
        print("✓ 'turn_number' index created successfully")
    except Exception as e:
        print(f"✗ Error creating 'turn_number' index: {e}")

    print("\n" + "="*70)
    print("Index creation complete!")
    print("="*70)
    print("\nYou can now use these filters and operations:")
    print("  Filters:")
    print("    --platform [chatgpt|claude|claude-projects]")
    print("    --interpretations")
    print("    Date filtering (date_from, date_to)")
    print("  Group By:")
    print("    platform, conversation_id, assistant_model")
    print("  Order By:")
    print("    timestamp, platform, conversation_title, turn_number")


if __name__ == "__main__":
    create_indexes()
