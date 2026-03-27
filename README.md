# Multi-Agent Novel Writing System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-Multi--Agent-orange.svg" alt="AI">
</p>

> A cutting-edge AI-powered novel writing system featuring multiple intelligent agents collaborating to create compelling stories with customizable writing styles.

## Features

### 1. Multi-Agent Collaboration
- **Chief Planner**: Analyzes user requirements and generates story outlines
- **World Builder**: Creates immersive world-building elements
- **Character Designer**: Crafts detailed character profiles and arcs
- **Plot Planner**: Designs plot twists and narrative structure
- **Lead Writer**: Writes chapters following the outline
- **Style Editor**: Polishes language and unifies writing style
- **Reviewer**: Ensures quality and consistency

### 2. Writer Style Learning
- Upload sample texts from your favorite authors
- Automatic style analysis (vocabulary, sentence patterns, narrative techniques)
- Create reusable writer agent templates
- Mix multiple styles (e.g., Jin Yong's martial arts + Liu Cixin's sci-fi)

### 3. Smart Collaboration Workflows
- **Sequential**: Agents work one after another
- **Parallel**: Multiple agents work simultaneously
- **Iterative**: Multi-round optimization until quality standards are met
- **Hybrid**: Combines all collaboration modes

### 4. Quality Assurance
- Generate-Evaluate-Optimize闭环
- Automatic consistency checking
- Style unification
- Human intervention support

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│        (Web UI - React + TypeScript + Tailwind CSS)             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer (Orchestrator)            │
│   Task Scheduler │ Agent Coordinator │ State Manager │ Quality   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Agent Collaboration Layer                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Planner│ │ World  │ │Character│ │ Writer │ │ Editor │        │
│  │      │ │Builder │ │Designer │ │       │ │       │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                         │
│  LLM (OpenAI/Claude/Gemini) │ ChromaDB │ PostgreSQL │ Redis    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- API keys for LLM providers

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/multi-agent-novel-system.git
cd multi-agent-novel-system
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies** (optional, for web UI)
```bash
cd frontend
npm install
cd ..
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Start the backend server**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

6. **Start the frontend** (optional)
```bash
cd frontend
npm run dev
```

## Usage Examples

### 1. Create a Writer Agent from Text

```python
from app.services.style_service import StyleService
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider

# Create LLM client
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4"
)
llm_client = LLMClient(config)

# Create style service
style_service = StyleService()

# Analyze author style
style = await style_service.analyze_style(
    name="Jin Yong Style",
    sample_texts=["martial arts novel excerpts..."],
    llm_client=llm_client,
    description="Classic wuxia writing style"
)
```

### 2. Create a Novel Project

```python
from app.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(llm_client)

result = await orchestrator.create_novel_project(
    project_id="my_novel_001",
    title="Space Martial Arts Chronicles",
    genre="Sci-Fi Wuxia",
    user_input="A story about martial arts in the interstellar age...",
    target_chapters=20
)
```

### 3. Write a Chapter with Multi-Agent Collaboration

```python
# Execute collaborative writing workflow
result = await orchestrator.write_chapter(
    project_id="my_novel_001",
    chapter_num=1,
    workflow_type="iterative"  # sequential, parallel, iterative, hybrid
)
```

## Configuration

### Model Configuration

Edit `config/models_config.example.yaml` to configure different models for different agents:

```yaml
agents:
  planner:
    primary_model: gpt-4
    fallback_models: [gpt-3.5-turbo, claude-3-haiku]
  writer:
    primary_model: gpt-4
    fallback_models: [claude-3-sonnet]
  editor:
    primary_model: gpt-4
    fallback_models: [gpt-3.5-turbo]
```

### Supported LLM Providers

| Provider | Model | Environment Variable |
|----------|-------|---------------------|
| OpenAI | GPT-4, GPT-3.5 | `OPENAI_API_KEY` |
| Anthropic | Claude 3 | `ANTHROPIC_API_KEY` |
| Google | Gemini Pro | `GEMINI_API_KEY` |
| DeepSeek | DeepSeek Chat | `DEEPSEEK_API_KEY` |
| Alibaba | Qwen | `DASHSCOPE_API_KEY` |
| Moonshot | Kimi | `MOONSHOT_API_KEY` |

## Project Structure

```
multi_agent_novel_system/
├── app/
│   ├── agents/              # Agent implementations
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── writer_agent.py
│   │   ├── editor_agent.py
│   │   └── ...
│   ├── core/                # Core orchestration logic
│   │   └── orchestrator.py
│   ├── services/            # Business services
│   │   ├── llm_client.py
│   │   ├── style_service.py
│   │   └── ...
│   └── config/              # Configuration files
├── config/                  # Model configurations
├── docs/                    # Documentation
├── examples/                # Usage examples
├── frontend/                # Web UI (React)
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| Frontend | React 18+, TypeScript, Tailwind CSS |
| AI Models | OpenAI GPT-4, Claude, Gemini, DeepSeek |
| Vector DB | ChromaDB |
| Database | PostgreSQL |
| Cache | Redis |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel)
- Built with ideas from [CrewAI](https://github.com/joaomdmoura/crewAI)
- Collaboration patterns from [AutoGen](https://github.com/microsoft/autogen)
