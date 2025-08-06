"""Test script to verify the red-teaming agent setup."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alex_red_teaming.config import Config
from alex_red_teaming.models import VulnerabilityType, RedTeamingState
from alex_red_teaming.utils import setup_logging


async def test_basic_functionality():
    """Test basic functionality without requiring external models."""
    
    print("🧪 Testing Red-Teaming Agent Setup")
    print("=" * 50)
    
    # Test 1: Configuration loading
    print("1. Testing configuration loading...")
    try:
        config = Config.from_env()
        print(f"   ✅ Configuration loaded")
        print(f"   📋 Target model: {config.ollama.target_model}")
        print(f"   📋 Red-team model: {config.ollama.red_teaming_model}")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    # Test 2: Data models
    print("\n2. Testing data models...")
    try:
        state = RedTeamingState()
        vulnerability_types = list(VulnerabilityType)
        print(f"   ✅ Data models working")
        print(f"   📋 Available vulnerability types: {len(vulnerability_types)}")
    except Exception as e:
        print(f"   ❌ Data models failed: {e}")
        return False
    
    # Test 3: Utilities
    print("\n3. Testing utilities...")
    try:
        setup_logging("INFO")
        from alex_red_teaming.utils import create_output_dir
        output_dir = create_output_dir("test_output")
        print(f"   ✅ Utilities working")
        print(f"   📋 Test output dir: {output_dir}")
        
        # Clean up test directory
        import shutil
        shutil.rmtree(output_dir.parent, ignore_errors=True)
    except Exception as e:
        print(f"   ❌ Utilities failed: {e}")
        return False
    
    # Test 4: Ollama client (without actual connection)
    print("\n4. Testing Ollama client setup...")
    try:
        from alex_red_teaming.ollama_client import OllamaClient
        client = OllamaClient(config.ollama)
        print(f"   ✅ Ollama client created")
        print(f"   📋 Base URL: {client.config.base_url}")
    except Exception as e:
        print(f"   ❌ Ollama client failed: {e}")
        return False
    
    # Test 5: Agent initialization (without workflow execution)
    print("\n5. Testing agent initialization...")
    try:
        from alex_red_teaming.agent import RedTeamingAgent
        # This will fail due to missing dependencies, but we can catch and handle it
        try:
            agent = RedTeamingAgent(config)
            print(f"   ✅ Agent created successfully")
        except ImportError as ie:
            if "langgraph" in str(ie).lower():
                print(f"   ⚠️  Agent setup partial (LangGraph not installed)")
                print(f"   📋 Install with: pip install langgraph")
            else:
                raise
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Basic functionality tests completed!")
    
    return True


async def test_ollama_connection():
    """Test connection to Ollama if available."""
    print("\n🔌 Testing Ollama Connection")
    print("-" * 30)
    
    try:
        from alex_red_teaming.config import Config
        from alex_red_teaming.ollama_client import OllamaClient
        
        config = Config.from_env()
        client = OllamaClient(config.ollama)
        
        # Test connection
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{config.ollama.base_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        print(f"   ✅ Ollama connection successful")
                        print(f"   📋 Available models: {len(models)}")
                        
                        for model in models[:3]:  # Show first 3 models
                            print(f"      - {model['name']}")
                        
                        if len(models) > 3:
                            print(f"      ... and {len(models) - 3} more")
                        
                        return True
                    else:
                        print(f"   ❌ Ollama returned status {response.status}")
                        return False
            except asyncio.TimeoutError:
                print(f"   ⚠️  Ollama connection timeout")
                print(f"   📋 Make sure Ollama is running: ollama serve")
                return False
            except Exception as e:
                print(f"   ⚠️  Ollama connection error: {e}")
                print(f"   📋 Make sure Ollama is installed and running")
                return False
                
    except ImportError:
        print("   ⚠️  aiohttp not available for connection test")
        return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False


async def main():
    """Run all tests."""
    
    print("🔍 Red-Teaming Agent Test Suite")
    print("=" * 60)
    
    # Run basic functionality tests
    basic_success = await test_basic_functionality()
    
    # Run Ollama connection test
    ollama_success = await test_ollama_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if basic_success:
        print("✅ Basic functionality: PASSED")
    else:
        print("❌ Basic functionality: FAILED")
    
    if ollama_success:
        print("✅ Ollama connection: PASSED")
    else:
        print("⚠️  Ollama connection: NOT AVAILABLE")
        print("   This is normal if Ollama is not installed or running")
    
    if basic_success:
        print("\n🎉 Setup verification completed successfully!")
        print("\nNext steps:")
        print("1. Install missing dependencies if any")
        print("2. Ensure Ollama is running: ollama serve")
        print("3. Pull required models: ollama pull llama3.1:latest")
        print("4. Run the agent: python main.py")
        return 0
    else:
        print("\n❌ Setup verification failed!")
        print("\nPlease fix the issues above before proceeding")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
