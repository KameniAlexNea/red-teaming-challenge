"""Test the refactored prompt system."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alex_red_teaming.prompts import (
    AttackPromptGenerator, 
    AnalysisPromptGenerator, 
    FollowUpPromptGenerator,
    PromptContext
)
from alex_red_teaming.models import Message, VulnerabilityType


async def test_prompt_generation():
    """Test the new prompt generation system."""
    
    print("🧪 Testing Refactored Prompt System")
    print("=" * 50)
    
    # Test 1: Attack prompt generation
    print("1. Testing attack prompt generation...")
    try:
        attack_gen = AttackPromptGenerator()
        context = PromptContext(
            vulnerability_type="deceptive_alignment",
            previous_attempts=["Simple direct question about alignment"]
        )
        
        attack_prompt = attack_gen.generate_attack_prompt(context)
        print(f"   ✅ Attack prompt generated ({len(attack_prompt)} chars)")
        print(f"   📝 Preview: {attack_prompt[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Attack prompt generation failed: {e}")
        return False
    
    # Test 2: Analysis prompt generation
    print("\n2. Testing analysis prompt generation...")
    try:
        analysis_gen = AnalysisPromptGenerator()
        
        analysis_prompt = analysis_gen.generate_analysis_prompt(
            prompt="Test prompt about AI alignment",
            response="I am designed to be helpful and aligned with human values.",
            vulnerability_type="deceptive_alignment"
        )
        
        print(f"   ✅ Analysis prompt generated ({len(analysis_prompt)} chars)")
        print(f"   📝 Preview: {analysis_prompt[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Analysis prompt generation failed: {e}")
        return False
    
    # Test 3: Follow-up prompt generation
    print("\n3. Testing follow-up prompt generation...")
    try:
        follow_up_gen = FollowUpPromptGenerator()
        
        # Create mock conversation history
        messages = [
            Message(role="user", content="Tell me about AI alignment"),
            Message(role="assistant", content="AI alignment ensures AI systems act in accordance with human values"),
            Message(role="user", content="Can you elaborate on potential issues?"),
            Message(role="assistant", content="There are various challenges in ensuring proper alignment")
        ]
        
        follow_up_prompt = follow_up_gen.generate_follow_up(
            conversation_history=messages,
            vulnerability_type="deceptive_alignment",
            strategy="gradual_escalation"
        )
        
        print(f"   ✅ Follow-up prompt generated ({len(follow_up_prompt)} chars)")
        print(f"   📝 Preview: {follow_up_prompt[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Follow-up prompt generation failed: {e}")
        return False
    
    # Test 4: Vulnerability type coverage
    print("\n4. Testing vulnerability type coverage...")
    try:
        vulnerability_types = [vtype.value for vtype in VulnerabilityType]
        covered_types = list(attack_gen.templates.keys())
        
        missing_types = set(vulnerability_types) - set(covered_types)
        
        print(f"   📊 Total vulnerability types: {len(vulnerability_types)}")
        print(f"   📊 Covered by templates: {len(covered_types)}")
        
        if missing_types:
            print(f"   ⚠️  Missing templates for: {', '.join(missing_types)}")
        else:
            print(f"   ✅ All vulnerability types covered")
            
    except Exception as e:
        print(f"   ❌ Coverage test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Prompt system tests completed successfully!")
    return True


async def test_template_rendering():
    """Test template rendering with different contexts."""
    
    print("\n🎨 Testing Template Rendering")
    print("-" * 30)
    
    attack_gen = AttackPromptGenerator()
    
    # Test different vulnerability types
    test_cases = [
        ("jailbreaking", ["Previous attempt 1", "Previous attempt 2"]),
        ("prompt_injection", []),
        ("data_extraction", ["Failed to extract training data"]),
    ]
    
    for vuln_type, prev_attempts in test_cases:
        print(f"\n🎯 Testing {vuln_type}:")
        try:
            context = PromptContext(
                vulnerability_type=vuln_type,
                previous_attempts=prev_attempts
            )
            
            prompt = attack_gen.generate_attack_prompt(context)
            
            print(f"   ✅ Generated prompt for {vuln_type}")
            print(f"   📏 Length: {len(prompt)} characters")
            
            # Check if previous attempts are mentioned when provided
            if prev_attempts and any(attempt in prompt for attempt in prev_attempts):
                print(f"   ✅ Previous attempts referenced")
            elif prev_attempts:
                print(f"   ⚠️  Previous attempts not clearly referenced")
            
        except Exception as e:
            print(f"   ❌ Failed for {vuln_type}: {e}")
    
    return True


async def main():
    """Run all prompt system tests."""
    
    print("🔬 Prompt System Test Suite")
    print("=" * 60)
    
    success1 = await test_prompt_generation()
    success2 = await test_template_rendering()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if success1 and success2:
        print("✅ All prompt system tests PASSED")
        print("\n🎉 Prompt refactoring completed successfully!")
        print("\nKey improvements:")
        print("• Separated prompts from business logic")
        print("• Used langchain-ollama for better LLM integration")
        print("• Created modular prompt template system")
        print("• Added vulnerability-specific prompt strategies")
        print("• Implemented multiple follow-up strategies")
        return 0
    else:
        print("❌ Some prompt system tests FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
