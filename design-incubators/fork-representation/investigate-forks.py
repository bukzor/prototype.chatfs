#!/usr/bin/env python3
"""
Investigate how Claude.ai API represents forked conversations.

Usage:
    ./investigate-forks.py <conversation_uuid>

This script will:
1. Fetch the conversation data
2. Print the raw JSON structure
3. Identify any fork-related fields
4. Document how forks are represented
"""

import json
import sys
from pathlib import Path

# Add unofficial-claude-api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "unofficial-claude-api"))

from claude_api import Client


def investigate_conversation(uuid: str):
    """Fetch and analyze conversation structure for fork information."""
    client = Client()

    print(f"Fetching conversation: {uuid}\n")

    # Fetch conversation
    conversation = client.get_conversation(uuid)

    print("=" * 80)
    print("FULL RAW RESPONSE")
    print("=" * 80)
    print(json.dumps(conversation, indent=2))
    print()

    # Look for fork-related fields
    print("=" * 80)
    print("FORK-RELATED FIELDS")
    print("=" * 80)

    fork_keywords = ["fork", "parent", "branch", "ancestor", "child", "thread"]

    def search_dict(obj, path=""):
        """Recursively search for fork-related keys."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if any(keyword in key.lower() for keyword in fork_keywords):
                    print(f"Found: {current_path} = {value}")
                search_dict(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_dict(item, f"{path}[{i}]")

    search_dict(conversation)

    print()
    print("=" * 80)
    print("CONVERSATION METADATA")
    print("=" * 80)
    metadata = {
        k: v for k, v in conversation.items() if not isinstance(v, (dict, list))
    }
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./investigate-forks.py <conversation_uuid>")
        print("\nTo find a forked conversation UUID:")
        print("1. Go to claude.ai and create a fork in a conversation")
        print("2. The URL will show the conversation UUID")
        print("3. Pass that UUID to this script")
        sys.exit(1)

    investigate_conversation(sys.argv[1])
