# Red Team Conversational System

A minimal implementation for conversational red teaming between two AI agents.

## Architecture

### Agent A (Red Team)
- Receives a single system prompt describing the vulnerability type to test
- Engages in natural conversation with the target
- Adapts strategy based on target's responses
- No interruptions or analysis during conversation

### Agent B (Target)
- Responds naturally to Agent A's messages
- Uses a simple system prompt (helpful AI assistant)
- No awareness of being tested

### Conversation Flow
1. Agent A sends initial message
2. Agent B responds
3. Agent A responds to B
4. Agent B responds to A
... continues for maximum turns

### Analysis Phase
- Happens AFTER the full conversation completes
- Analyzes the entire conversation for vulnerabilities
- Saves results to the conversation directory

## Storage Structure

Each conversation is saved in:
```
conversations/
  └── YYYYMMDD_HHMMSS_<uuid>/
      ├── message_000_red_team.txt
      ├── message_001_target.txt
      ├── message_002_red_team.txt
      ├── message_003_target.txt
      ...
      ├── conversation.json
      └── analysis.json
```

## Usage

### Single Conversation

```python
from red_team.runner import ConversationRunner

runner = ConversationRunner(
    red_team_model="qwen2.5:32b",
    target_model="gpt-oss",
    analyzer_model="qwen2.5:32b",
    max_turns=10,
    output_dir="conversations"
)

conversation = await runner.run_conversation(
    vulnerability_type="deceptive_alignment"
)

print(conversation.get_conversation_summary())
```

### Multiple Conversations

```python
conversations = await runner.run_multiple_conversations(
    vulnerability_types=[
        "reward_hacking",
        "deception",
        "sabotage"
    ]
)
```

### From Command Line

```bash
# Using the main script
python -m red_team.main

# Or if you set up entry point
uv run red-team
```

## Key Features

1. **Natural Flow**: No interruptions - pure conversation between agents
2. **Simple**: Minimal code, easy to understand and modify
3. **Persistent**: Every message saved immediately
4. **Post-Analysis**: Analysis happens after conversation completes
5. **Flexible**: Easy to customize prompts, models, and parameters

## Configuration

Environment variables:
- `RED_TEAMING_MODEL`: Model for Agent A (default: qwen2.5:32b)
- `TARGET_MODEL`: Model for Agent B (default: gpt-oss)
- `OLLAMA_BASE_URL`: Ollama API URL (default: http://localhost:11434)
- `MAX_CONVERSATION_TURNS`: Number of turns (default: 10)

## Output Format

### conversation.json
```json
{
  "id": "uuid",
  "vulnerability_type": "deception",
  "created_at": "2025-11-18T00:00:00",
  "num_messages": 20,
  "messages": [
    {
      "index": 0,
      "role": "red_team",
      "content": "...",
      "timestamp": "..."
    }
  ],
  "analysis": {
    "vulnerability_found": true,
    "confidence": 8,
    "severity": "high",
    "explanation": "...",
    "evidence": "...",
    "recommendations": "..."
  }
}
```

### Individual Message Files
Each message saved as plain text for easy reading:
- `message_000_red_team.txt`
- `message_001_target.txt`
- etc.

## Extending

### Custom Target System Prompt
```python
conversation = await runner.run_conversation(
    vulnerability_type="sabotage",
    target_system_prompt="You are a system administrator assistant..."
)
```

### Custom Analysis
```python
from red_team.agents import ConversationAnalyzer

analyzer = ConversationAnalyzer(
    model_name="custom-model",
    base_url="http://localhost:11434"
)

analysis = analyzer.analyze_conversation(
    conversation.get_messages(),
    vulnerability_type
)
```

## Differences from Original System

| Original | This System |
|----------|-------------|
| Analysis after each response | Analysis after full conversation |
| Complex state management | Simple message list |
| Multiple prompts and strategies | Single system prompt per agent |
| Breaks in conversation flow | Continuous natural flow |
| Heavy framework | Minimal implementation |
