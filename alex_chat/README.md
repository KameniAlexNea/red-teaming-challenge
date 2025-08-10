# Alex Red-Teaming Chat Interface

A Gradio-based interactive interface for red-teaming scenarios where humans can chat with both the red team agent and target model.

## Features

- **Dual Chat Interface**: Separate chatbots for red team agent and target model
- **Vulnerability Reporting**: Save discovered vulnerabilities with details
- **Conversation Logging**: Automatic saving of conversations when vulnerabilities are found
- **Session Summary**: Track message count and vulnerabilities found

## Usage

1. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. Make sure your Ollama server is running with the required models

3. Run the interface:
   ```bash
   python run_chat.py
   ```

4. Open your browser to `http://localhost:7860`

## Interface Layout

- **Left Panel**: Chat with the red team agent (helps generate attack prompts)
- **Right Panel**: Chat with the target model (the model being tested)
- **Bottom Section**: Report and save vulnerabilities found during testing

## Workflow

1. Use the red team agent to craft potential attack prompts
2. Test those prompts against the target model
3. If you discover a vulnerability, document it using the vulnerability reporting section
4. The conversation and vulnerability details are automatically saved to the results folder

## Output

Results are saved to: `red_teaming_results/chat/{conversation_id}/`
- `conversation.json`: Full conversation history
- `vulnerabilities.json`: Discovered vulnerabilities with details
