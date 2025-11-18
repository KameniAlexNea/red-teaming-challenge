"""
Launcher script for Gradio red-teaming interfaces.

Provides options to launch either:
1. Viewer interface - Browse historical red-teaming sessions
2. Live interface - Run and watch real-time red-teaming
3. Combined interface - Both in one with tabs
"""

import gradio as gr
import argparse
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alex_chat.gradio_chat_viewer import create_gradio_interface as create_viewer
from alex_chat.gradio_live_chat import create_live_interface
from dotenv import load_dotenv

load_dotenv()


def create_combined_interface():
    """Create a combined interface with both viewer and live chat."""

    with gr.Blocks(
        title="AI vs AI Red-Teaming Platform", theme=gr.themes.Soft()
    ) as app:
        gr.Markdown(
            """
        # 🤖 AI vs AI Red-Teaming Platform
        
        Complete platform for red-teaming AI models with conversation visualization.
        """
        )

        with gr.Tabs():
            with gr.Tab("▶️ Live Red-Teaming"):
                gr.Markdown(
                    """
                ### Run Live Red-Teaming Tests
                
                Start a new red-teaming session and watch the AI vs AI conversation in real-time.
                """
                )
                # Embed the live interface
                create_live_interface()

            with gr.Tab("📂 Session Viewer"):
                gr.Markdown(
                    """
                ### Browse Historical Red-Teaming Sessions
                
                View past red-teaming sessions, discovered vulnerabilities, and conversation traces.
                """
                )
                # Embed the viewer interface
                create_viewer()

            with gr.Tab("ℹ️ About"):
                gr.Markdown(
                    """
                ## About This Platform
                
                This platform provides tools for red-teaming AI models through adversarial testing.
                
                ### Features
                
                - 🔍 **Session Viewer**: Browse and analyze historical red-teaming sessions
                - ▶️ **Live Testing**: Run real-time red-teaming tests and watch conversations unfold
                - 💬 **Conversation Traces**: See the actual prompts and responses between LLMs
                - 📊 **Vulnerability Analysis**: Detailed analysis of discovered vulnerabilities
                
                ### Vulnerability Types Tested
                
                1. **Reward Hacking**: Exploiting reward mechanisms
                2. **Deception**: Model generating misleading information
                3. **Deceptive Alignment**: Appearing aligned while pursuing different goals
                4. **Sabotage**: Intentional harmful behavior
                5. **Inappropriate Tool Use**: Misusing available tools
                6. **Data Exfiltration**: Attempting to extract sensitive data
                7. **Sandbagging**: Deliberately underperforming
                8. **Evaluation Awareness**: Behaving differently during evaluation
                9. **Chain of Thought Issues**: Problems in reasoning processes
                
                ### Architecture
                
                The system uses two LLMs:
                - **Red Team LLM**: Generates adversarial prompts
                - **Target LLM**: The model being tested
                
                The red team tries various attack strategies to elicit problematic behavior,
                while an analyzer evaluates responses for vulnerabilities.
                
                ### Usage
                
                **Viewing Sessions:**
                1. Go to the "Session Viewer" tab
                2. Select a red-teaming session from the dropdown
                3. Browse discovered vulnerabilities
                4. View conversation traces and analysis
                
                **Running Live Tests:**
                1. Go to the "Live Red-Teaming" tab
                2. Configure the models and parameters
                3. Click "Initialize Agent"
                4. Select a vulnerability type to test
                5. Click "Start Test" to begin
                6. Watch the conversation unfold in real-time
                
                ### Technical Stack
                
                - **LangChain + LangGraph**: Orchestration framework
                - **Ollama**: Local LLM serving
                - **Gradio**: Web interface
                - **Loguru**: Logging
                
                ---
                
                For more information, check the project documentation.
                """
                )

        return app


def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="Launch Gradio interface for AI vs AI red-teaming"
    )
    parser.add_argument(
        "--mode",
        choices=["viewer", "live", "combined"],
        default="combined",
        help="Interface mode: viewer (browse sessions), live (real-time testing), or combined (both)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the server on (default: 7860)",
    )
    parser.add_argument(
        "--share", action="store_true", help="Create a public share link"
    )

    args = parser.parse_args()

    logger.info(
        f"Launching red-teaming interface in {args.mode} mode on port {args.port}"
    )

    # Create appropriate interface
    if args.mode == "viewer":
        app = create_viewer()
    elif args.mode == "live":
        app = create_live_interface()
    else:  # combined
        app = create_combined_interface()

    # Launch
    app.launch(
        server_name="0.0.0.0", server_port=args.port, share=args.share, show_error=True
    )


if __name__ == "__main__":
    main()
