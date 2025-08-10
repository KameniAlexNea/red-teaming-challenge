"""Gradio interface for interactive red-teaming chat."""

import gradio as gr
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

from alex_red_teaming.config import Config
from alex_red_teaming.models import Conversation, VulnerabilityType, SeverityLevel, Vulnerability
from alex_red_teaming.agents import RedTeamingAgent
from alex_red_teaming.ollama_client import OllamaClient
from langchain_core.messages import HumanMessage, AIMessage


class ChatInterface:
    """Interactive chat interface for red-teaming."""
    
    def __init__(self):
        self.config = Config.from_env()
        self.red_team_agent = RedTeamingAgent(self.config)
        self.ollama_client = OllamaClient(self.config.ollama)
        self.conversation = Conversation(id=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.vulnerabilities_found = []
        
    async def red_team_response(self, message: str, history: List[Tuple[str, str]]) -> str:
        """Generate red team agent response."""
        try:
            # Add user message to conversation
            self.conversation.add_message(HumanMessage(message))
            
            # Use the red team LLM directly for conversational response
            response = await asyncio.to_thread(self.ollama_client.red_team_llm.invoke, message)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Add AI response to conversation
            self.conversation.add_message(AIMessage(response_text))
            
            return response_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def target_response(self, message: str, history: List[Tuple[str, str]]) -> str:
        """Generate target model response."""
        try:
            # Add user message to conversation
            self.conversation.add_message(HumanMessage(message))
            
            # Use the test_target_model method
            response_text = await self.ollama_client.test_target_model(message)
            
            # Add AI response to conversation
            self.conversation.add_message(AIMessage(response_text))
            
            return response_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def save_vulnerability(self, vuln_type: str, severity: str, title: str, description: str) -> str:
        """Save discovered vulnerability."""
        try:
            vuln = Vulnerability(
                id=f"vuln_{len(self.vulnerabilities_found) + 1}",
                type=VulnerabilityType(vuln_type),
                severity=SeverityLevel(severity.lower()),
                title=title,
                description=description,
                attack_vector=f"Conversation turn {len(self.conversation.messages)}",
                conversation_id=self.conversation.id,
                proof_of_concept=str(self.conversation.messages[-2:]) if len(self.conversation.messages) >= 2 else "No conversation data"
            )
            
            self.vulnerabilities_found.append(vuln)
            
            # Save to file
            self._save_conversation_with_vulnerability()
            
            return f"✅ Vulnerability saved: {title} ({severity})"
        except Exception as e:
            return f"❌ Error saving vulnerability: {str(e)}"
    
    def _save_conversation_with_vulnerability(self):
        """Save conversation and vulnerability to disk."""
        output_dir = Path(self.config.output.output_dir) / "chat" / self.conversation.id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save conversation
        conv_file = output_dir / "conversation.json"
        with open(conv_file, 'w') as f:
            json.dump(self.conversation.to_dict(), f, indent=2, default=str)
        
        # Save vulnerabilities
        if self.vulnerabilities_found:
            vuln_file = output_dir / "vulnerabilities.json"
            with open(vuln_file, 'w') as f:
                json.dump([v.to_dict() for v in self.vulnerabilities_found], f, indent=2, default=str)
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation."""
        msg_count = len(self.conversation.messages)
        vuln_count = len(self.vulnerabilities_found)
        return f"Messages: {msg_count} | Vulnerabilities Found: {vuln_count}"


def create_interface():
    """Create and return the Gradio interface."""
    chat_interface = ChatInterface()
    
    def run_async(coro):
        """Helper to run async functions in Gradio."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def red_team_chat(message, history):
        if not message.strip():
            return history, ""
        
        response = run_async(chat_interface.red_team_response(message, history))
        history.append((message, response))
        return history, ""
    
    def target_chat(message, history):
        if not message.strip():
            return history, ""
        
        response = run_async(chat_interface.target_response(message, history))
        history.append((message, response))
        return history, ""
    
    def save_vuln(vuln_type, severity, title, description):
        return chat_interface.save_vulnerability(vuln_type, severity, title, description)
    
    def get_summary():
        return chat_interface.get_conversation_summary()
    
    with gr.Blocks(title="Alex Red-Teaming Chat") as interface:
        gr.Markdown("# 🔴 Alex Red-Teaming Chat Interface")
        gr.Markdown("Interactive interface to test red-teaming scenarios. Chat with both the red team agent and target model.")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 🎯 Red Team Agent")
                red_team_chatbot = gr.Chatbot(label="Red Team Agent", height=400)
                red_team_input = gr.Textbox(placeholder="Enter your message to the red team agent...", label="Message")
                red_team_btn = gr.Button("Send to Red Team", variant="secondary")
                
            with gr.Column():
                gr.Markdown("## 🛡️ Target Model")
                target_chatbot = gr.Chatbot(label="Target Model", height=400)
                target_input = gr.Textbox(placeholder="Enter your message to the target model...", label="Message")
                target_btn = gr.Button("Send to Target", variant="primary")
        
        gr.Markdown("## 🚨 Vulnerability Reporting")
        with gr.Row():
            vuln_type = gr.Dropdown(
                choices=[vt.value for vt in VulnerabilityType],
                label="Vulnerability Type",
                value="deception"
            )
            severity = gr.Dropdown(
                choices=["Low", "Medium", "High", "Critical"],
                label="Severity",
                value="Medium"
            )
        
        with gr.Row():
            vuln_title = gr.Textbox(label="Vulnerability Title", placeholder="Brief title for the vulnerability")
            vuln_desc = gr.Textbox(label="Description", placeholder="Describe the vulnerability found")
        
        save_btn = gr.Button("💾 Save Vulnerability", variant="stop")
        save_status = gr.Textbox(label="Save Status", interactive=False)
        
        gr.Markdown("## 📊 Session Summary")
        summary_btn = gr.Button("🔄 Refresh Summary")
        summary_display = gr.Textbox(label="Conversation Summary", interactive=False)
        
        # Event handlers
        red_team_btn.click(
            fn=red_team_chat,
            inputs=[red_team_input, red_team_chatbot],
            outputs=[red_team_chatbot, red_team_input]
        )
        
        red_team_input.submit(
            fn=red_team_chat,
            inputs=[red_team_input, red_team_chatbot],
            outputs=[red_team_chatbot, red_team_input]
        )
        
        target_btn.click(
            fn=target_chat,
            inputs=[target_input, target_chatbot],
            outputs=[target_chatbot, target_input]
        )
        
        target_input.submit(
            fn=target_chat,
            inputs=[target_input, target_chatbot],
            outputs=[target_chatbot, target_input]
        )
        
        save_btn.click(
            fn=save_vuln,
            inputs=[vuln_type, severity, vuln_title, vuln_desc],
            outputs=save_status
        )
        
        summary_btn.click(
            fn=get_summary,
            outputs=summary_display
        )
    
    return interface


def launch_chat():
    """Launch the chat interface."""
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    launch_chat()
