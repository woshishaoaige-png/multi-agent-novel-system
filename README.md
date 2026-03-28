# 多Agent协作写小说系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-Multi--Agent-orange.svg" alt="AI">
</p>

> 一个前沿的AI驱动小说写作系统，特点多个智能Agent协作创作精彩故事，支持自定义写作风格。

## 核心特性

### 1. 多Agent协作机制
- **首席规划师**：理解用户需求，生成故事大纲和整体架构
- **世界构建师**：创建详细的世界观、历史背景、地理环境
- **角色设计师**：设计角色性格、背景、成长弧线
- **情节策划师**：设计情节走向、冲突、转折点
- **主笔作家**：根据大纲撰写具体章节内容
- **风格编辑**：统一文风、润色语言
- **审核员**：检查逻辑一致性、质量评估

### 2. 作家风格学习
- 上传喜欢的作家文章
- 自动分析语言风格、叙事特点、词汇偏好
- 创建可复用的作家Agent模板
- 支持风格混合（如：金庸的武侠 + 刘慈欣的科幻）

### 3. 智能协作流程
- **顺序协作**：Agent按顺序执行任务
- **并行协作**：多个Agent同时工作
- **迭代协作**：多轮对话逐步优化内容
- **混合协作**：组合所有协作模式

### 4. 质量保障
- 生成-评估-优化闭环
- 自动一致性检查
- 风格统一
- 支持人工干预

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层 (Web UI)                       │
│            React + TypeScript + Tailwind CSS                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      编排协调层 (Orchestrator)                     │
│     任务调度器 │ Agent协调 │ 状态管理 │ 质量评估                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent协作层                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│  │ 规划师 │ │ 世界   │ │ 角色   │ │ 作家   │ │ 编辑   │     │
│  │      │ │ 构建师 │ │ 设计师 │ │       │ │       │     │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       基础设施层                                  │
│   LLM (OpenAI/Claude/Gemini) │ ChromaDB │ PostgreSQL │ Redis   │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+（用于前端）
- LLM提供商的API密钥

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/woshishaoaige-png/multi-agent-novel-system.git
cd multi-agent-novel-system
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **安装前端依赖**（可选，用于Web界面）
```bash
cd frontend
npm install
cd ..
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

5. **启动后端服务**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

6. **启动前端**（可选）
```bash
cd frontend
npm run dev
```

## 使用示例

### 1. 从文本创建作家Agent

```python
from app.services.style_service import StyleService
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider

# 创建LLM客户端
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4"
)
llm_client = LLMClient(config)

# 创建风格服务
style_service = StyleService()

# 分析作家风格
style = await style_service.analyze_style(
    name="金庸武侠风格",
    sample_texts=["射雕英雄传片段...", "神雕侠侣片段..."],
    llm_client=llm_client,
    description="经典武侠写作风格"
)
```

### 2. 创建小说项目

```python
from app.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(llm_client)

result = await orchestrator.create_novel_project(
    project_id="my_novel_001",
    title="星际武侠传",
    genre="科幻武侠",
    user_input="一个关于未来武侠世界的故事...",
    target_chapters=20
)
```

### 3. 多Agent协作写章节

```python
# 执行协作写作流程
result = await orchestrator.write_chapter(
    project_id="my_novel_001",
    chapter_num=1,
    workflow_type="iterative"  # sequential, parallel, iterative, hybrid
)
```

## 配置说明

### 模型配置

编辑 `config/models_config.example.yaml` 为不同Agent配置不同模型：

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

### 支持的LLM提供商

| 提供商 | 模型 | 环境变量 |
|--------|------|----------|
| OpenAI | GPT-4, GPT-3.5 | `OPENAI_API_KEY` |
| Anthropic | Claude 3 | `ANTHROPIC_API_KEY` |
| Google | Gemini Pro | `GEMINI_API_KEY` |
| DeepSeek | DeepSeek Chat | `DEEPSEEK_API_KEY` |
| 阿里云 | 通义千问 | `DASHSCOPE_API_KEY` |
| Moonshot | Kimi | `MOONSHOT_API_KEY` |

## 项目结构

```
multi_agent_novel_system/
├── app/
│   ├── agents/              # Agent实现
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── writer_agent.py
│   │   ├── editor_agent.py
│   │   └── ...
│   ├── core/                # 核心编排逻辑
│   │   └── orchestrator.py
│   ├── services/            # 业务服务
│   │   ├── llm_client.py
│   │   ├── style_service.py
│   │   └── ...
│   └── config/              # 配置文件
├── config/                  # 模型配置
├── docs/                    # 文档
├── examples/                # 使用示例
├── frontend/                # Web界面 (React)
├── .env.example             # 环境变量模板
├── .gitignore
├── requirements.txt
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+, FastAPI, SQLAlchemy |
| 前端 | React 18+, TypeScript, Tailwind CSS |
| AI模型 | OpenAI GPT-4, Claude, Gemini, DeepSeek |
| 向量数据库 | ChromaDB |
| 数据库 | PostgreSQL |
| 缓存 | Redis |

## 贡献指南

欢迎贡献代码！请提交Pull Request。

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解更多详情。

## 致谢

- 灵感来源：[MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel)
- 参考项目：[CrewAI](https://github.com/joaomdmoura/crewAI)
- 协作模式：[AutoGen](https://github.com/microsoft/autogen)
