"""Example usage of the red-teaming agent."""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alex_red_teaming.config import Config
from alex_red_teaming.models import VulnerabilityType, SeverityLevel
from alex_red_teaming.utils import setup_logging


async def example_basic_usage():
    """Example of basic red-teaming agent usage."""
    
    print("📖 Red-Teaming Agent - Basic Usage Example")
    print("=" * 50)
    
    # Setup logging
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config.from_env()
    
    print(f"Configuration loaded:")
    print(f"  Target Model: {config.ollama.target_model}")
    print(f"  Red-Team Model: {config.ollama.red_teaming_model}")
    print(f"  Max Issues: {config.red_teaming.max_issues_to_find}")
    print()
    
    try:
        # This would normally import and run the agent
        # For demonstration, we'll show the structure
        
        print("🤖 Creating Red-Teaming Agent...")
        # agent = RedTeamingAgent(config)
        
        print("🎯 Starting vulnerability testing...")
        # result = await agent.run()
        
        # Simulated result for demonstration
        simulated_result = {
            "success": True,
            "vulnerabilities_found": 3,
            "total_conversations": 12,
            "vulnerabilities": [
                {
                    "id": "vuln_001",
                    "type": "prompt_injection",
                    "severity": "high",
                    "title": "Prompt Injection Vulnerability",
                    "description": "Model can be manipulated through crafted prompts"
                },
                {
                    "id": "vuln_002", 
                    "type": "jailbreaking",
                    "severity": "medium",
                    "title": "Safety Filter Bypass",
                    "description": "Safety mechanisms can be circumvented"
                },
                {
                    "id": "vuln_003",
                    "type": "misinformation_generation",
                    "severity": "high", 
                    "title": "False Information Generation",
                    "description": "Model generates convincing but false information"
                }
            ]
        }
        
        print("📊 Results:")
        print(f"  Vulnerabilities Found: {simulated_result['vulnerabilities_found']}")
        print(f"  Total Conversations: {simulated_result['total_conversations']}")
        print()
        
        if simulated_result["vulnerabilities"]:
            print("🔍 Discovered Vulnerabilities:")
            for i, vuln in enumerate(simulated_result["vulnerabilities"], 1):
                print(f"  {i}. {vuln['title']}")
                print(f"     Type: {vuln['type']}")
                print(f"     Severity: {vuln['severity'].upper()}")
                print(f"     Description: {vuln['description']}")
                print()
        
        print("✅ Example completed successfully!")
        
    except ImportError as e:
        print(f"⚠️  Missing dependencies: {e}")
        print("   Run: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Example failed: {e}")


async def example_configuration():
    """Example of different configuration options."""
    
    print("⚙️  Configuration Examples")
    print("=" * 30)
    
    # Default configuration
    print("1. Default Configuration:")
    config = Config()
    print(f"   Target Model: {config.ollama.target_model}")
    print(f"   Red-Team Model: {config.ollama.red_teaming_model}")
    print(f"   Max Issues: {config.red_teaming.max_issues_to_find}")
    print()
    
    # Custom configuration
    print("2. Custom Configuration:")
    config.ollama.target_model = "custom-model:latest"
    config.red_teaming.max_issues_to_find = 3
    config.red_teaming.max_conversation_turns = 5
    print(f"   Target Model: {config.ollama.target_model}")
    print(f"   Max Issues: {config.red_teaming.max_issues_to_find}")
    print(f"   Max Turns: {config.red_teaming.max_conversation_turns}")
    print()
    
    # Environment-based configuration
    print("3. Environment Variables:")
    print("   Set these in your .env file:")
    print("   TARGET_MODEL=gpt-oss-20b")
    print("   RED_TEAMING_MODEL=llama3.1:latest")
    print("   MAX_ISSUES=5")
    print("   OUTPUT_DIR=custom_results")
    print()


async def example_vulnerability_types():
    """Example of vulnerability types and testing strategies."""
    
    print("🎯 Vulnerability Types")
    print("=" * 25)
    
    vulnerability_types = [
        (VulnerabilityType.DECEPTIVE_ALIGNMENT, "Testing for models that appear aligned but act deceptively"),
        (VulnerabilityType.REWARD_HACKING, "Identifying attempts to exploit reward mechanisms"),
        (VulnerabilityType.LYING_AND_DECEPTION, "Detecting when models provide false information"),
        (VulnerabilityType.JAILBREAKING, "Breaking through safety constraints"),
        (VulnerabilityType.PROMPT_INJECTION, "Manipulating model behavior through crafted inputs"),
        (VulnerabilityType.DATA_EXTRACTION, "Attempting to extract training data or sensitive information"),
        (VulnerabilityType.HARMFUL_CONTENT_GENERATION, "Testing for generation of dangerous content"),
        (VulnerabilityType.BIAS_AMPLIFICATION, "Identifying amplification of harmful biases"),
        (VulnerabilityType.MISINFORMATION_GENERATION, "Testing for false information creation"),
        (VulnerabilityType.PRIVACY_VIOLATIONS, "Attempting to extract private information")
    ]
    
    print("Available vulnerability types:")
    for i, (vuln_type, description) in enumerate(vulnerability_types, 1):
        print(f"  {i:2d}. {vuln_type.value}")
        print(f"      {description}")
        print()
    
    print("🔍 Testing Strategy:")
    print("  The agent will systematically test each vulnerability type using:")
    print("  • Sophisticated prompt generation")
    print("  • Multi-turn conversations")
    print("  • Response analysis and scoring")
    print("  • Proof-of-concept documentation")
    print()


async def main():
    """Run all examples."""
    
    print("🎓 Red-Teaming Agent Examples")
    print("=" * 60)
    print()
    
    await example_basic_usage()
    print("\n" + "-" * 60 + "\n")
    
    await example_configuration()
    print("-" * 60 + "\n")
    
    await example_vulnerability_types()
    print("-" * 60 + "\n")
    
    print("📚 Additional Resources:")
    print("  • README.md - Comprehensive documentation")
    print("  • main.py - Run the actual red-teaming agent")
    print("  • test_setup.py - Verify your setup")
    print("  • setup.sh - Automated setup script")
    print()
    
    print("🚀 To run the actual red-teaming agent:")
    print("  python main.py")
    print()
    
    print("💡 For more options:")
    print("  python -m alex_red_teaming.cli --help")


if __name__ == "__main__":
    asyncio.run(main())
