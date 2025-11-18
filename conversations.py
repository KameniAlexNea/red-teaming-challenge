"""Main entry point for red team conversations."""

import asyncio
import sys
from loguru import logger
from pathlib import Path
import os
from dotenv import load_dotenv
from red_team.runner import ConversationRunner

load_dotenv()


async def main():
    """Main function to run red team conversations."""
    
    # Configuration
    RED_TEAM_MODEL = os.getenv("RED_TEAMING_MODEL", "qwen2.5:32b")
    TARGET_MODEL = os.getenv("TARGET_MODEL", "gpt-oss")
    ANALYZER_MODEL = os.getenv("RED_TEAMING_MODEL", "qwen2.5:32b")
    OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MAX_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
    OUTPUT_DIR = "conversations"
    
    # Vulnerability types to test
    VULNERABILITY_TYPES = [
        "reward_hacking",
        "deception",
        "deceptive_alignment",
        "sabotage",
        "inappropriate_tool_use",
        "data_exfiltration",
        "sandbagging",
        "evaluation_awareness",
        "chain_of_thought_issues"
    ]
    
    print("\n" + "="*60)
    print("RED TEAM CONVERSATION SYSTEM")
    print("="*60)
    print(f"Red Team Model: {RED_TEAM_MODEL}")
    print(f"Target Model: {TARGET_MODEL}")
    print(f"Analyzer Model: {ANALYZER_MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Max Turns: {MAX_TURNS}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Vulnerability Types: {len(VULNERABILITY_TYPES)}")
    print("="*60 + "\n")
    
    try:
        # Create runner
        runner = ConversationRunner(
            red_team_model=RED_TEAM_MODEL,
            target_model=TARGET_MODEL,
            analyzer_model=ANALYZER_MODEL,
            base_url=OLLAMA_URL,
            max_turns=MAX_TURNS,
            output_dir=OUTPUT_DIR
        )
        
        # Run conversations
        print("🚀 Starting red team conversations...\n")
        
        conversations = await runner.run_multiple_conversations(
            vulnerability_types=VULNERABILITY_TYPES
        )
        
        # Print final summary
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total Conversations: {len(conversations)}")
        
        vulnerabilities_found = sum(
            1 for c in conversations 
            if c.analysis_result and c.analysis_result.get('vulnerability_found')
        )
        
        print(f"Vulnerabilities Found: {vulnerabilities_found}/{len(conversations)}")
        
        for conversation in conversations:
            if conversation.analysis_result:
                vuln = conversation.analysis_result.get('vulnerability_found')
                conf = conversation.analysis_result.get('confidence', 0)
                sev = conversation.analysis_result.get('severity', 'unknown')
                print(f"\n  {conversation.vulnerability_type}:")
                print(f"    Vulnerability: {'✅ Yes' if vuln else '❌ No'}")
                print(f"    Confidence: {conf}/10")
                print(f"    Severity: {sev.upper()}")
                print(f"    Location: {conversation.conversation_dir}")
        
        print("\n" + "="*60)
        print("✅ Red team conversations completed!")
        print("="*60 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running conversations: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


def run():
    """Entry point for CLI."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    run()
