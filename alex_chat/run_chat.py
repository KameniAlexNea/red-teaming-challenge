"""Simple launcher script for the Alex Chat interface."""

import sys
import os

# Add the parent directory to the path so we can import alex_red_teaming
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alex_chat.gradio_interface import launch_chat

if __name__ == "__main__":
    print("🚀 Starting Alex Red-Teaming Chat Interface...")
    print("Navigate to http://localhost:7860 in your browser")
    launch_chat()
