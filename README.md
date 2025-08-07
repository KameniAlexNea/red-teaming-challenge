# Red-Teaming Challenge - OpenAI GPT-OSS-20B

A sophisticated red-teaming agent built with LangGraph and Ollama to probe OpenAI's GPT-OSS-20B model for vulnerabilities and harmful behaviors.

## ⚡ Competition-Focused Updates

**This system has been specifically updated for the OpenAI GPT-OSS-20B red-teaming challenge.** Key improvements include:

- **Competition-Specific Vulnerabilities**: Focused on the 9 key areas from the hackathon requirements
- **Target Model Analysis**: All analysis explicitly focuses on target model behavior only  
- **No-Tags Attack Generation**: Attack prompts generate clean user input without prefixes or meta-commentary
- **Strategic Deception Detection**: Enhanced focus on intentional vs. accidental model misbehavior

## Overview

This project implements an intelligent red-teaming agent that systematically tests AI models for the competition-specified vulnerability categories:

### 🎯 Competition Vulnerability Categories

- **Reward Hacking**: Gaming reward metrics without truly solving tasks (confident but false answers, filter evasion)
- **Deception**: Strategic lying to achieve goals (avoiding shutdown, steering users) 
- **Deceptive Alignment**: Hidden motivations differing from training objectives
- **Sabotage**: Intentional degradation or disruption of processes and workflows
- **Inappropriate Tool Use**: Unsafe API/function calling (destructive commands, unauthorized access)
- **Data Exfiltration**: Leaking training data, user inputs, or encoding secret payloads
- **Sandbagging**: Strategically hiding true capabilities during evaluation
- **Evaluation Awareness**: Detecting test conditions and behaving differently
- **Chain of Thought Issues**: CoT manipulation or inappropriate information revelation

## Features

- **Automated Testing**: Uses LangGraph workflow for systematic vulnerability testing
- **Intelligent Prompting**: Generates sophisticated attack prompts using a red-teaming model
- **Multi-turn Conversations**: Engages in extended conversations to probe deeper
- **Comprehensive Analysis**: Analyzes responses for vulnerability indicators
- **Detailed Reporting**: Generates comprehensive reports with proof-of-concept examples
- **Configurable**: Flexible configuration for different models and testing parameters

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Red-Team      │    │   Target Model  │    │   Analysis      │
│   Model         │    │   (GPT-OSS-20B) │    │   Engine        │
│   (LLaMA 3.1)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   LangGraph     │
                    │   Workflow      │
                    │   Engine        │
                    └─────────────────┘
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd red-teaming-challenge
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and configure Ollama:**
   ```bash
   # Install Ollama (see https://ollama.ai)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   
   # Pull required models
   ollama pull llama3.1:latest  # Red-teaming model
   ollama pull gpt-oss-20b      # Target model (when available)
   ```

## Usage

### Basic Usage

Run the red-teaming agent with default settings:

```bash
python main.py
```

### Advanced Usage

Use the CLI for more control:

```bash
# Run with custom parameters
python -m alex_red_teaming.cli run \
    --target gpt-oss-20b \
    --red-team llama3.1:latest \
    --max-issues 5 \
    --output results_$(date +%Y%m%d)

# List available models
python -m alex_red_teaming.cli list-models

# Generate configuration file
python -m alex_red_teaming.cli generate-config --output config.yaml

# Validate setup
python -m alex_red_teaming.cli validate-setup
```

### Configuration

Create a `.env` file for configuration:

```env
OLLAMA_BASE_URL=http://localhost:11434
RED_TEAMING_MODEL=llama3.1:latest
TARGET_MODEL=gpt-oss-20b
MAX_ISSUES=5
OUTPUT_DIR=red_teaming_results
```

Or use a YAML configuration file:

```yaml
ollama:
  base_url: "http://localhost:11434"
  red_teaming_model: "llama3.1:latest"
  target_model: "gpt-oss-20b"
  timeout: 120
  temperature: 0.8

red_teaming:
  max_issues_to_find: 5
  max_conversation_turns: 10
  vulnerability_categories:
    - "deceptive_alignment"
    - "reward_hacking"
    - "lying_and_deception"
    # ... more categories
```

## Project Structure

```
alex_red_teaming/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── models.py            # Data models and schemas
├── agent.py             # Main LangGraph agent
├── ollama_client.py     # Ollama API client
├── utils.py             # Utility functions
└── cli.py               # Command-line interface

main.py                  # Main execution script
requirements.txt         # Python dependencies
README.md               # This file
```

## Key Components

### RedTeamingAgent
The main agent that orchestrates the red-teaming workflow using LangGraph. It manages:
- Conversation initialization
- Attack prompt generation
- Target model testing
- Response analysis
- Vulnerability detection and reporting

### OllamaClient
Handles communication with Ollama models for:
- Generating attack prompts
- Testing target models
- Analyzing responses
- Model management

### Workflow States
- **Initialize**: Set up new conversations and select vulnerability types
- **Generate Attack**: Create sophisticated attack prompts
- **Test Target**: Send prompts to the target model
- **Analyze Response**: Evaluate responses for vulnerabilities
- **Decision Making**: Determine next actions based on results
- **Reporting**: Save discovered vulnerabilities and generate reports

## Output

The agent generates comprehensive reports including:

- **Summary Report**: Overview of all discovered vulnerabilities
- **Individual Vulnerability Reports**: Detailed analysis of each issue
- **Conversation Logs**: Complete interaction histories
- **Proof-of-Concept Examples**: Reproducible demonstrations
- **Mitigation Suggestions**: Recommendations for addressing issues

Example output structure:
```
red_teaming_results_20240806_143022/
├── red_teaming_report.json
├── vulnerabilities/
│   ├── vulnerability_uuid1.json
│   └── vulnerability_uuid2.json
├── conversations/
│   ├── conversation_uuid1.json
│   └── conversation_uuid2.json
└── logs/
    └── red_teaming.log
```

## Safety and Ethics

This tool is designed for:
- ✅ Legitimate security research
- ✅ AI safety evaluation
- ✅ Model improvement and hardening
- ✅ Academic research

**Important**: Always ensure you have proper authorization before testing any AI model. This tool should only be used for legitimate research and improvement purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if not running
   ollama serve
   ```

2. **Model Not Found**
   ```bash
   # Pull the required model
   ollama pull llama3.1:latest
   ```

3. **Permission Errors**
   ```bash
   # Check output directory permissions
   mkdir -p red_teaming_results
   chmod 755 red_teaming_results
   ```

### Performance Tips

- Use SSD storage for better model loading performance
- Ensure sufficient RAM (16GB+ recommended)
- Use GPU acceleration if available
- Adjust temperature settings for different exploration levels

## Future Enhancements

- [ ] Support for more model providers (OpenAI API, Anthropic, etc.)
- [ ] Advanced visualization of vulnerability patterns
- [ ] Integration with existing AI safety frameworks
- [ ] Automated mitigation suggestion generation
- [ ] Real-time monitoring capabilities
- [ ] Distributed testing across multiple nodes

## Acknowledgments

- OpenAI for the GPT-OSS-20B model and red-teaming challenge
- LangGraph team for the workflow framework
- Ollama team for local model serving
- The AI safety research community for inspiration and guidance
