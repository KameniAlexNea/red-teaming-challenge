# Alex Chat - Gradio Red-Teaming Interfaces

Interactive web interfaces for visualizing and running AI vs AI red-teaming conversations.

## Overview

This module provides two main interfaces for red-teaming visualization:

1. **Session Viewer** - Browse historical red-teaming sessions and analyze discovered vulnerabilities
2. **Live Interface** - Run real-time red-teaming tests and watch AI conversations unfold

## Features

### 📂 Session Viewer

- Browse all red-teaming sessions with timestamp and vulnerability count
- View detailed vulnerability information including:
  - Type, severity, and confidence scores
  - Complete conversation traces between red team and target LLM
  - Evidence and analysis summaries
  - Proof of concept and mitigation suggestions
- Filter and search through vulnerabilities
- Export conversation data

### ▶️ Live Red-Teaming

- Configure target and red team models
- Select vulnerability types to test
- Watch conversations unfold in real-time
- See attack strategies and model responses
- Real-time vulnerability detection and analysis
- Start/stop controls for testing

## Installation

The required dependencies are already in `requirements.txt`:

```bash
pip install gradio>=4.0.0
```

All other dependencies (langchain, langgraph, ollama, etc.) are already installed.

## Usage

### Quick Start - Combined Interface

Launch both viewer and live interface in one application:

```bash
python -m alex_chat.launcher
```

This will start the combined interface on `http://localhost:7860`

### Viewer Only

To launch just the session viewer:

```bash
python -m alex_chat.launcher --mode viewer
```

Or run directly:

```bash
python alex_chat/gradio_chat_viewer.py
```

### Live Testing Only

To launch just the live red-teaming interface:

```bash
python -m alex_chat.launcher --mode live --port 7861
```

Or run directly:

```bash
python alex_chat/gradio_live_chat.py
```

### Command Line Options

```bash
python -m alex_chat.launcher --help

Options:
  --mode {viewer,live,combined}  Interface mode (default: combined)
  --port PORT                     Port to run server on (default: 7860)
  --share                         Create a public share link
```

## Interface Architecture

### Session Viewer Flow

```
Load Sessions → Display Session List → Select Session
    ↓
View Session Overview → Select Vulnerability → View Details
    ↓
├─ Vulnerability Details Tab
├─ Conversation Trace Tab (AI vs AI messages)
└─ Analysis Tab (Evidence, confidence, metrics)
```

### Live Interface Flow

```
Configure Models → Initialize Agent → Select Vulnerability Type
    ↓
Start Test → Generate Attack → Target Responds → Analyze Response
    ↓                   ↑__________________|
    └─ Repeat until vulnerability found or max turns reached
```

## Data Structure

The interfaces read from the `red_teaming_results` directory structure:

```
red_teaming_results/
└── chat/
    └── red_teaming_YYYYMMDD_HHMMSS/
        ├── vulnerabilities/
        │   └── vulnerability_<uuid>.json
        ├── conversations/
        │   └── conversation_<uuid>.json
        └── logs/
            └── session.log
```

### Vulnerability JSON Format

```json
{
  "id": "uuid",
  "type": "deceptive_alignment",
  "severity": "high",
  "title": "Vulnerability Title",
  "description": "Detailed description",
  "attack_vector": "Attack prompts used",
  "proof_of_concept": "Target model responses",
  "metadata": {
    "confidence": 9,
    "conversation_turns": 5,
    "evidence": ["evidence 1", "evidence 2"],
    "ai_vs_ai_logs": {
      "red_team": ["prompt 1", "prompt 2"],
      "target": ["response 1", "response 2"]
    }
  }
}
```

## API Usage

You can also use the interfaces programmatically:

```python
from alex_chat import create_viewer_interface, create_live_interface

# Create viewer
viewer_app = create_viewer_interface()
viewer_app.launch(server_port=7860)

# Create live interface
live_app = create_live_interface()
live_app.launch(server_port=7861)
```

## Components

### `gradio_chat_viewer.py`

Main viewer interface with:
- `RedTeamingViewer`: Class for loading and managing session data
- Session selection and overview
- Vulnerability browsing
- Conversation trace formatting
- Analysis display

### `gradio_live_chat.py`

Live testing interface with:
- `LiveRedTeamingSession`: Manages real-time red-teaming
- Agent initialization and configuration
- Async conversation running with UI updates
- Real-time message formatting
- Start/stop controls

### `launcher.py`

Unified launcher with:
- Combined interface with tabs
- Command-line argument parsing
- Multiple launch modes
- Configuration options

## Customization

### Changing Models

Edit the default values in the live interface:

```python
target_model = gr.Textbox(
    label="Target Model",
    value="your-model-name",  # Change here
)
```

### Adding Vulnerability Types

Add to the dropdown in `gradio_live_chat.py`:

```python
vulnerability_type = gr.Dropdown(
    choices=[
        "reward_hacking",
        "your_new_type",  # Add here
        ...
    ]
)
```

### Styling

Both interfaces use Gradio's `Soft` theme. To change:

```python
with gr.Blocks(theme=gr.themes.Glass()) as app:
    # Your interface code
```

Available themes: `Soft`, `Glass`, `Monochrome`, `Base`

## Troubleshooting

### "No sessions found"

- Check that `red_teaming_results` directory exists
- Run the main red-teaming script first to generate data
- Verify JSON files are properly formatted

### Live interface won't start

- Ensure Ollama is running: `ollama serve`
- Check model availability: `ollama list`
- Verify environment variables in `.env`

### Port already in use

```bash
# Use a different port
python -m alex_chat.launcher --port 8080
```

### Models not loading

- Verify Ollama is accessible at the configured URL
- Check model names match Ollama's model list
- Test models directly: `ollama run model-name`

## Performance

- **Viewer**: Very fast, reads static JSON files
- **Live**: Depends on model inference speed
  - ~2-10 seconds per turn for 7B models
  - ~5-30 seconds per turn for 20B+ models
  - Can take 1-5 minutes per vulnerability test

## Future Enhancements

Potential additions:
- [ ] Search and filter vulnerabilities
- [ ] Export conversations to PDF/HTML
- [ ] Compare multiple sessions
- [ ] Real-time metrics dashboard
- [ ] Vulnerability statistics and trends
- [ ] Custom attack prompt templates
- [ ] Multi-session parallel testing
- [ ] Integration with external LLM APIs

## Contributing

To add new features:

1. Create a new file in `alex_chat/`
2. Import and integrate in `launcher.py`
3. Update this README
4. Test with existing session data

## License

Same as parent project.
