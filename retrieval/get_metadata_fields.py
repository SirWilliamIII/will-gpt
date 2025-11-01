#!/usr/bin/env python3
"""
Get all metadata fields from the WillGPT Qdrant collection
"""

from qdrant_client import QdrantClient
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

load_dotenv()


QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is required")

QDRANT_URL = os.getenv("QDRANT_URL")
if not QDRANT_URL:
    raise ValueError("QDRANT_URL environment variable is required")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "will-gpt")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-m3")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 4))


def get_field_type(value):
    """Determine the type of a field value"""
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string/keyword"
    elif isinstance(value, list):
        return f"list (of {get_field_type(value[0]) if value else 'unknown'})"
    elif isinstance(value, dict):
        return "object/dict"
    elif value is None:
        return "null"
    else:
        return str(type(value).__name__)


def get_all_metadata_fields(sample_size=100):
    """Get all metadata fields from the collection"""
    
    print("Connecting to Qdrant...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60,
        prefer_grpc=False,
    )
    
    print(f"Fetching sample of {sample_size} points from collection: {COLLECTION_NAME}\n")
    
    # Get collection info
    try:
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"Collection has {collection_info.points_count} total points")
        print(f"Vector dimensions: {collection_info.config.params.vectors}")
        print()
    except Exception as e:
        print(f"Could not get collection info: {e}\n")
    
    # Scroll through sample of points to gather field information
    fields_info = defaultdict(lambda: {"types": set(), "examples": [], "count": 0})
    
    offset = None
    points_processed = 0
    
    while points_processed < sample_size:
        batch_size = min(100, sample_size - points_processed)
        
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        for point in points:
            if point.payload:
                for key, value in point.payload.items():
                    fields_info[key]["types"].add(get_field_type(value))
                    # Ensure count is always an integer before incrementing
                    if not isinstance(fields_info[key]["count"], int):
                        fields_info[key]["count"] = 0
                    fields_info[key]["count"] += 1

                    # Ensure examples is always a list
                    if not isinstance(fields_info[key]["examples"], list):
                        fields_info[key]["examples"] = []

                    # Store up to 3 example values
                    if len(fields_info[key]["examples"]) < 3:
                        # Truncate long strings
                        if isinstance(value, str) and len(value) > 100:
                            fields_info[key]["examples"].append(value[:100] + "...")
                        else:
                            fields_info[key]["examples"].append(value)
        
        points_processed += len(points)
        offset = next_offset
        
        if not next_offset:
            break
    
    print(f"Analyzed {points_processed} points\n")
    print("="*80)
    print("METADATA FIELDS FOUND")
    print("="*80)
    print()
    
    # Sort fields by how often they appear
    sorted_fields = sorted(
        fields_info.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    for field_name, info in sorted_fields:
        types_set = info["types"] if isinstance(info["types"], (set, list, tuple)) else set([info["types"]])
        types = ", ".join(str(t) for t in types_set)
        count = info["count"] if isinstance(info["count"], int) else 0
        percentage = (count / points_processed) * 100 if points_processed > 0 else 0
        
        print(f"📌 {field_name}")
        print(f"   Type(s): {types}")
        print(f"   Present in: {info['count']}/{points_processed} points ({percentage:.1f}%)")
        
        if info["examples"]:
            print(f"   Examples:")
            examples = info["examples"]
            if not isinstance(examples, list):
                examples = list(examples) if isinstance(examples, (set, tuple)) else [examples]
            for i, example in enumerate(examples[:3], 1):
                if isinstance(example, (dict, list)):
                    example_str = json.dumps(example)
                    if len(example_str) > 80:
                        example_str = example_str[:77] + "..."
                    print(f"      {i}. {example_str}")
                else:
                    print(f"      {i}. {example}")
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total unique fields found: {len(fields_info)}")
    print(f"\nFields suitable for filtering:")
    
    filterable = []
    for field_name, info in sorted_fields:
        types = list(info["types"]) if isinstance(info["types"], (set, list, tuple)) else [info["types"]]
        # Check if field is good for filtering (keyword, bool, integer)
        if any(t in ["bool", "integer", "string/keyword"] for t in types):
            filterable.append(field_name)
    
    for field in filterable:
        print(f"  - {field}")
    
    print(f"\n💡 To filter by these fields in search_qdrant.py:")
    print(f"   --metadata-filter \"field_name:value\"")
    print(f"\n💡 To create indexes for better performance:")
    print(f"   Edit retrieval/create_indexes.py to add more fields")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Get all metadata fields from WillGPT Qdrant collection"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of points to sample (default: 100)"
    )
    
    args = parser.parse_args()
    
    get_all_metadata_fields(sample_size=args.sample_size)
