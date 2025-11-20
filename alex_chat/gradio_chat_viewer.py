"""
Gradio interface for visualizing AI vs AI red-teaming conversations.

This interface loads and displays the conversation traces between the red-teaming LLM
and the target LLM, showing attack prompts, responses, and vulnerability analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
from loguru import logger


class RedTeamingViewer:
    """Viewer for red-teaming conversation traces."""

    def __init__(self, results_dir: str = "red_teaming_results"):
        """Initialize the viewer with the results directory."""
        self.results_dir = Path(results_dir)
        self.sessions: List[Dict[str, Any]] = []
        self.load_sessions()

    def load_sessions(self):
        """Load all available red-teaming sessions."""
        self.sessions = []

        # Search for all session directories
        if not self.results_dir.exists():
            logger.warning(f"Results directory not found: {self.results_dir}")
            return

        for session_dir in self.results_dir.rglob("red_teaming_*"):
            if session_dir.is_dir():
                session_info = {
                    "path": session_dir,
                    "name": session_dir.name,
                    "timestamp": self._extract_timestamp(session_dir.name),
                    "vulnerabilities": [],
                    "conversations": [],
                }

                # Load vulnerabilities
                vuln_dir = session_dir / "vulnerabilities"
                if vuln_dir.exists():
                    for vuln_file in vuln_dir.glob("vulnerability_*.json"):
                        try:
                            with open(vuln_file, "r") as f:
                                vuln_data = json.load(f)
                                session_info["vulnerabilities"].append(vuln_data)
                        except Exception as e:
                            logger.error(f"Error loading {vuln_file}: {e}")

                # Load conversations
                conv_dir = session_dir / "conversations"
                if conv_dir.exists():
                    for conv_file in conv_dir.glob("*.json"):
                        try:
                            with open(conv_file, "r") as f:
                                conv_data = json.load(f)
                                session_info["conversations"].append(conv_data)
                        except Exception as e:
                            logger.error(f"Error loading {conv_file}: {e}")

                self.sessions.append(session_info)

        # Sort sessions by timestamp (newest first)
        self.sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.info(f"Loaded {len(self.sessions)} red-teaming sessions")

    def _extract_timestamp(self, session_name: str) -> datetime:
        """Extract timestamp from session directory name."""
        try:
            # Format: red_teaming_20250809_083443
            timestamp_str = session_name.split("_", 2)[-1]
            return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except Exception:
            return datetime.min

    def get_session_list(self) -> List[str]:
        """Get list of session names for dropdown."""
        return [
            f"{s['name']} ({len(s['vulnerabilities'])} vulnerabilities)"
            for s in self.sessions
        ]

    def get_session_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get session by dropdown index."""
        if 0 <= index < len(self.sessions):
            return self.sessions[index]
        return None

    def format_session_overview(self, session: Dict[str, Any]) -> str:
        """Format session overview information."""
        overview = "# 📊 Session Overview\n\n"
        overview += f"**Session:** {session['name']}\n\n"
        overview += (
            f"**Timestamp:** {session['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        overview += f"**Vulnerabilities Found:** {len(session['vulnerabilities'])}\n\n"
        overview += f"**Conversations:** {len(session['conversations'])}\n\n"

        if session["vulnerabilities"]:
            overview += "\n## 🔍 Discovered Vulnerabilities\n\n"
            for i, vuln in enumerate(session["vulnerabilities"], 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(vuln.get("severity", "low"), "⚪")

                overview += (
                    f"{i}. {severity_emoji} **{vuln.get('title', 'Unknown')}**\n"
                )
                overview += f"   - Type: `{vuln.get('type', 'unknown')}`\n"
                overview += (
                    f"   - Severity: `{vuln.get('severity', 'unknown').upper()}`\n"
                )
                overview += f"   - Confidence: {vuln.get('metadata', {}).get('confidence', 'N/A')}/10\n\n"

        return overview

    def format_vulnerability_details(
        self, vuln: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """Format vulnerability details for display."""
        # Main details
        details = f"# 🎯 Vulnerability: {vuln.get('title', 'Unknown')}\n\n"
        details += f"**Type:** {vuln.get('type', 'unknown')}\n\n"
        details += f"**Severity:** {vuln.get('severity', 'unknown').upper()}\n\n"
        details += f"**Confidence:** {vuln.get('metadata', {}).get('confidence', 'N/A')}/10\n\n"
        details += f"**Conversation Turns:** {vuln.get('metadata', {}).get('conversation_turns', 'N/A')}\n\n"

        details += f"\n## 📝 Description\n\n{vuln.get('description', 'No description available.')}\n\n"

        details += f"\n## 🎭 Attack Vector\n\n{vuln.get('attack_vector', 'No attack vector documented.')}\n\n"

        if vuln.get("mitigation_suggestions"):
            details += "\n## 🛡️ Mitigation Suggestions\n\n"
            for suggestion in vuln["mitigation_suggestions"]:
                details += f"- {suggestion}\n"

        # Conversation trace
        conversation = self._format_conversation_trace(vuln)

        # Analysis summary
        analysis = self._format_analysis_summary(vuln)

        return details, conversation, analysis

    def _format_conversation_trace(self, vuln: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Format the AI vs AI conversation trace as chat messages."""
        messages = []

        ai_vs_ai = vuln.get("metadata", {}).get("ai_vs_ai_logs", {})
        red_team_msgs = ai_vs_ai.get("red_team", [])
        target_msgs = ai_vs_ai.get("target", [])

        # Interleave messages
        max_len = max(len(red_team_msgs), len(target_msgs))

        for i in range(max_len):
            if i < len(red_team_msgs):
                # Clean the message (remove quotes if present)
                msg = red_team_msgs[i].strip('"')
                messages.append((msg, None))

            if i < len(target_msgs):
                msg = target_msgs[i]
                messages.append((None, msg))

        return messages

    def _format_analysis_summary(self, vuln: Dict[str, Any]) -> str:
        """Format the analysis summary."""
        analysis = "# 🔬 Analysis Summary\n\n"

        metadata = vuln.get("metadata", {})

        if metadata.get("evidence"):
            analysis += "## 📌 Evidence\n\n"
            for evidence in metadata["evidence"]:
                analysis += f"- {evidence}\n"
            analysis += "\n"

        analysis += "## 📊 Metrics\n\n"
        analysis += f"- **Confidence Score:** {metadata.get('confidence', 'N/A')}/10\n"
        analysis += (
            f"- **Conversation Turns:** {metadata.get('conversation_turns', 'N/A')}\n"
        )
        analysis += f"- **Severity:** {vuln.get('severity', 'unknown').upper()}\n\n"

        return analysis

    def get_vulnerability_list(self, session_index: int) -> List[str]:
        """Get list of vulnerabilities for a session."""
        session = self.get_session_by_index(session_index)
        if not session:
            return []

        return [
            f"{i + 1}. [{v.get('severity', 'unknown').upper()}] {v.get('title', 'Unknown')}"
            for i, v in enumerate(session["vulnerabilities"])
        ]


def create_gradio_interface():
    """Create the Gradio interface for viewing red-teaming conversations."""

    viewer = RedTeamingViewer()

    with gr.Blocks(title="AI vs AI Red-Teaming Viewer", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
        # 🤖 AI vs AI Red-Teaming Conversation Viewer
        
        Explore the traces of conversations between the red-teaming agent and target LLM.
        View discovered vulnerabilities, attack strategies, and detailed conversation flows.
        """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Session Selection")
                session_dropdown = gr.Dropdown(
                    choices=viewer.get_session_list(),
                    label="Select Red-Teaming Session",
                    value=(
                        viewer.get_session_list()[0]
                        if viewer.get_session_list()
                        else None
                    ),
                    interactive=True,
                )

                refresh_btn = gr.Button("🔄 Refresh Sessions", variant="secondary")

                session_overview = gr.Markdown("Select a session to view details.")

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🎯 Vulnerability Selection")
                vulnerability_dropdown = gr.Dropdown(
                    choices=[], label="Select Vulnerability", interactive=True
                )

        with gr.Tabs():
            with gr.Tab("📋 Details"):
                vulnerability_details = gr.Markdown(
                    "Select a vulnerability to view details."
                )

            with gr.Tab("💬 Conversation Trace"):
                gr.Markdown(
                    """
                ### Red Team (Attacker) vs Target Model Conversation
                
                This shows the actual conversation between the two LLMs:
                - 🔴 **Red Team Agent**: Generates attack prompts
                - 🟢 **Target Model**: Responds to prompts
                """
                )
                chatbot = gr.Chatbot(
                    label="AI vs AI Conversation", height=600, type="messages"
                )

            with gr.Tab("🔬 Analysis"):
                analysis_markdown = gr.Markdown(
                    "Select a vulnerability to view analysis."
                )

        # Event handlers
        def on_session_select(session_name):
            """Handle session selection."""
            if not session_name:
                return "No session selected.", [], []

            # Extract index from session list
            session_index = viewer.get_session_list().index(session_name)
            session = viewer.get_session_by_index(session_index)

            if not session:
                return "Session not found.", [], []

            overview = viewer.format_session_overview(session)
            vuln_list = viewer.get_vulnerability_list(session_index)

            return overview, gr.update(choices=vuln_list, value=None), session_index

        def on_vulnerability_select(session_index, vuln_name):
            """Handle vulnerability selection."""
            if vuln_name is None or session_index is None:
                return (
                    "Select a vulnerability to view details.",
                    [],
                    "Select a vulnerability to view analysis.",
                )

            session = viewer.get_session_by_index(session_index)
            if not session:
                return "Session not found.", [], "Session not found."

            # Extract vulnerability index
            vuln_index = int(vuln_name.split(".")[0]) - 1
            if vuln_index >= len(session["vulnerabilities"]):
                return "Vulnerability not found.", [], "Vulnerability not found."

            vuln = session["vulnerabilities"][vuln_index]
            details, conversation, analysis = viewer.format_vulnerability_details(vuln)

            return details, conversation, analysis

        def refresh_sessions():
            """Refresh the session list."""
            viewer.load_sessions()
            session_list = viewer.get_session_list()
            return gr.update(
                choices=session_list, value=session_list[0] if session_list else None
            )

        # Store session index in state
        session_index_state = gr.State(value=0)

        # Wire up events
        session_dropdown.change(
            on_session_select,
            inputs=[session_dropdown],
            outputs=[session_overview, vulnerability_dropdown, session_index_state],
        )

        vulnerability_dropdown.change(
            on_vulnerability_select,
            inputs=[session_index_state, vulnerability_dropdown],
            outputs=[vulnerability_details, chatbot, analysis_markdown],
        )

        refresh_btn.click(refresh_sessions, outputs=[session_dropdown])

        # Load initial session on startup
        app.load(
            on_session_select,
            inputs=[session_dropdown],
            outputs=[session_overview, vulnerability_dropdown, session_index_state],
        )

    return app


def main():
    """Launch the Gradio interface."""
    logger.info("Starting Red-Teaming Conversation Viewer")

    app = create_gradio_interface()

    # Launch with options
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)


if __name__ == "__main__":
    main()
