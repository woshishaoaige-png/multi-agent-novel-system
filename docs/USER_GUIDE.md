# 多Agent协作写小说系统 - 使用指南

## 目录

1. [系统概述](#系统概述)
2. [安装配置](#安装配置)
3. [快速开始](#快速开始)
4. [Agent模型配置](#agent模型配置)
5. [高级用法](#高级用法)
6. [API参考](#api参考)

---

## 系统概述

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层 (Web UI)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      编排协调层 (Orchestrator)                     │
│         任务调度 │ Agent协调 │ 状态管理 │ 质量监控                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Agent协作层                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │
│  │规划师  │ │世界    │ │角色    │ │情节    │ │作家    │ │编辑  │ │
│  │(P)     │ │(W)     │ │(C)     │ │(Pl)    │ │(Wr)    │ │(E)   │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    作家风格系统 (Style System)                     │
│           风格分析 │ 风格存储 │ 风格迁移 │ 风格混合                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent角色说明

| Agent | 角色 | 职责 |
|-------|------|------|
| **PlannerAgent** | 首席规划师 | 理解需求、生成大纲、协调Agent |
| **WorldBuilderAgent** | 世界构建师 | 创建世界观、地理、历史、文化 |
| **CharacterAgent** | 角色设计师 | 设计角色、关系网、成长弧线 |
| **WriterAgent** | 主笔作家 | 撰写章节内容 |
| **EditorAgent** | 风格编辑 | 润色内容、统一文风 |

---

## 安装配置

### 1. 环境要求

- Python 3.8+
- 支持的LLM API

### 2. 安装依赖

```bash
cd multi_agent_novel_system
pip install aiohttp pyyaml
```

### 3. 配置API密钥

设置环境变量：

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-key"

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-your-key"

# Google Gemini
export GEMINI_API_KEY="your-key"

# DeepSeek
export DEEPSEEK_API_KEY="your-key"

# 阿里云百炼（通义千问）- 获取地址: https://bailian.console.aliyun.com/
export DASHSCOPE_API_KEY="your-key"

# Kimi（月之暗面）- 获取地址: https://platform.moonshot.cn/
export MOONSHOT_API_KEY="your-key"
```

### 4. 支持的模型提供商

| 提供商 | 说明 | 模型示例 | 中文支持 |
|--------|------|---------|----------|
| **OpenAI** | GPT系列 | gpt-4, gpt-3.5-turbo | 一般 |
| **Anthropic** | Claude系列 | claude-3-opus, claude-3-sonnet | 一般 |
| **Google** | Gemini系列 | gemini-pro, gemini-ultra | 一般 |
| **DeepSeek** | 深度求索 | deepseek-chat, deepseek-coder | 良好 |
| **阿里云百炼** | 通义千问 | qwen-plus, qwen-turbo, qwen-long | 优秀 |
| **Kimi** | 月之暗面 | moonshot-v1-8k, moonshot-v1-128k | 优秀 |

---

## 快速开始

### 示例1: 最简单的使用

```python
import asyncio
import os
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.core.orchestrator import AgentOrchestrator
from app.agents.base_agent import AgentRole

async def main():
    # 1. 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 2. 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 3. 创建小说项目
    result = await orchestrator.create_novel_project(
        project_id="my_first_novel",
        title="我的第一部小说",
        genre="奇幻",
        user_input="我想写一个关于魔法学院的成长故事...",
        target_chapters=10
    )
    
    print(f"项目创建成功: {result['project_id']}")
    
    # 4. 撰写第一章
    chapter = await orchestrator.write_chapter(
        project_id="my_first_novel",
        chapter_num=1
    )
    print(f"第一章完成: {chapter['word_count']}字")
    
    await llm_client.close()

asyncio.run(main())
```

---

## Agent模型配置

### 核心概念

系统支持**为每个Agent单独配置不同的大模型**：

```python
# 不同Agent可以使用不同模型
{
    "planner": "gpt-4",           # 规划师用最强模型
    "world_builder": "claude-3-opus",  # 世界构建师用Claude
    "writer": "gpt-4",            # 作家用GPT-4
    "editor": "gpt-3.5-turbo"     # 编辑用便宜的模型
}
```

### 方法1: 通过配置文件（推荐）

#### 步骤1: 复制并编辑配置文件

```bash
cp config/models_config.example.yaml config/models_config.yaml
```

#### 步骤2: 编辑 `config/models_config.yaml`

```yaml
# 定义可用模型
models:
  gpt-4:
    provider: openai
    model_name: gpt-4
    capabilities:
      - general
      - creative
      - analysis
    cost_tier: expensive

  claude-3-opus:
    provider: anthropic
    model_name: claude-3-opus-20240229
    capabilities:
      - general
      - creative
      - analysis
    cost_tier: expensive

  gpt-3.5-turbo:
    provider: openai
    model_name: gpt-3.5-turbo
    capabilities:
      - general
      - fast
    cost_tier: cheap

# 配置Agent使用哪个模型
agent_models:
  planner:
    primary_model: gpt-4
    fallback_models:
      - claude-3-opus
    max_retries: 3

  writer:
    primary_model: gpt-4
    fallback_models:
      - claude-3-opus
    max_retries: 3

  editor:
    primary_model: gpt-3.5-turbo
    fallback_models: []
```

#### 步骤3: 代码中加载配置

```python
import os
from app.config.agent_model_config import init_model_registry
from app.services.llm_client import create_multi_client_from_config

# 加载配置文件
registry = init_model_registry("config/models_config.yaml")

# 创建多LLM客户端
api_keys = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY")
}
multi_client = create_multi_client_from_config(
    "config/models_config.yaml",
    api_keys
)
```

---

### 方法2: 代码中直接配置

#### 示例1: 创建Agent时指定模型

```python
from app.core.orchestrator import AgentOrchestrator
from app.agents.base_agent import AgentRole

orchestrator = AgentOrchestrator(llm_client)

# 为每个Agent指定不同的模型
planner = orchestrator.create_agent(
    AgentRole.PLANNER,
    agent_id="my_planner",
    model_id="gpt-4"  # 指定模型
)

world_builder = orchestrator.create_agent(
    AgentRole.WORLD_BUILDER,
    agent_id="my_world",
    model_id="claude-3-opus"  # 指定不同模型
)

writer = orchestrator.create_agent(
    AgentRole.WRITER,
    agent_id="my_writer",
    model_id="gpt-4"
)

editor = orchestrator.create_agent(
    AgentRole.STYLE_EDITOR,
    agent_id="my_editor",
    model_id="gpt-3.5-turbo"  # 简单任务用便宜的模型
)
```

#### 示例2: 创建项目时配置模型

```python
# 创建项目时指定Agent模型
result = await orchestrator.create_novel_project(
    project_id="custom_model_project",
    title="自定义模型项目",
    genre="科幻",
    user_input="一个关于星际探险的故事...",
    target_chapters=20,
    agent_models={
        "planner": "gpt-4",
        "world_builder": "claude-3-opus",
        "character_designer": "gpt-4",
        "writer": "gpt-4",
        "editor": "gpt-3.5-turbo"
    }
)
```

#### 示例3: 动态切换模型

```python
# 运行时切换Agent模型
orchestrator.set_agent_model("my_planner", "claude-3-opus")

# 或者直接在Agent上切换
planner.switch_model("gemini-pro")
```

---

### 方法3: 任务级别模型配置

```python
# 创建工作流时指定任务使用的模型
workflow = orchestrator.create_workflow(
    workflow_id="custom_workflow",
    name="自定义工作流",
    workflow_type=WorkflowType.SEQUENTIAL,
    project_id="test_project",
    tasks_config=[
        {
            "type": "create_outline",
            "agent_id": planner.agent_id,
            "params": {"user_input": "..."},
            "model_id": "gpt-4"  # 指定任务使用GPT-4
        },
        {
            "type": "create_world",
            "agent_id": world_builder.agent_id,
            "params": {"genre": "奇幻"},
            "model_id": "claude-3-opus"  # 这个任务用Claude
        }
    ]
)
```

---

## 高级用法

### 1. 模型回退机制

如果主模型失败，系统会自动尝试备用模型：

```python
# 在配置中定义回退模型
agent_models:
  writer:
    primary_model: gpt-4
    fallback_models:
      - claude-3-opus  # 第一个备用
      - gemini-pro      # 第二个备用
    max_retries: 3
```

### 2. 成本优化策略

```python
# 根据任务复杂度选择模型
def get_model_for_task(task_type: str) -> str:
    if task_type in ["create_outline", "write_chapter"]:
        return "gpt-4"  # 复杂任务用强模型
    elif task_type in ["get_context", "simple_edit"]:
        return "gpt-3.5-turbo"  # 简单任务用便宜模型
    else:
        return "claude-3-sonnet"  # 中等任务
```

### 3. 模型使用统计

```python
# 获取模型使用统计
stats = orchestrator.get_model_stats()

print(f"总Agent数量: {stats['total_agents']}")
print(f"模型使用分布: {stats['model_usage']}")
print(f"可用模型: {stats['available_models']}")
```

### 4. 多提供商配置

```python
from app.services.llm_client import LLMClient, LLMConfig, MultiLLMClient

# 创建多个LLM客户端
clients = MultiLLMClient()

clients.add_client("openai", LLMClient(LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4"
)), is_default=True)

clients.add_client("anthropic", LLMClient(LLMConfig(
    provider=LLMProvider.ANTHROPIC,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-opus"
)))

# 按Agent角色自动选择
result = await clients.complete(
    prompt="...",
    agent_role="writer"  # 系统自动选择writer配置的模型
)
```

---

## API参考

### AgentOrchestrator

```python
class AgentOrchestrator:
    def __init__(self, llm_client, model_registry=None)
    
    # Agent管理
    def create_agent(role, agent_id=None, style=None, model_id=None) -> BaseAgent
    def set_agent_model(agent_id: str, model_id: str)
    def get_agent_model(agent_id: str) -> str
    
    # 项目管理
    async def create_novel_project(
        project_id, title, genre, user_input, 
        target_chapters=20, agent_models=None
    ) -> Dict
    
    async def write_chapter(
        project_id, chapter_num, writer_style=None, model_id=None
    ) -> Dict
    
    def get_project_status(project_id) -> Dict
    
    # 工作流
    def create_workflow(...) -> Workflow
    async def execute_workflow(workflow_id) -> Dict
    
    # 统计
    def get_model_stats() -> Dict
```

### AgentModelRegistry

```python
class AgentModelRegistry:
    def register_model(model_id: str, model_info: ModelInfo)
    def get_model(model_id: str) -> ModelInfo
    def set_agent_config(agent_role: str, config: AgentModelConfig)
    def get_agent_config(agent_role: str) -> AgentModelConfig
    def get_model_for_agent(agent_role, task_type=None) -> ModelInfo
    def find_best_model(capabilities, cost_constraint=None) -> ModelInfo
    def load_from_yaml(yaml_path: str)
    def save_to_yaml(yaml_path: str)
```

### LLMClient

```python
class LLMClient:
    def __init__(self, config: LLMConfig)
    
    async def complete(
        prompt, system_prompt=None, stream=False,
        model=None, temperature=None, max_tokens=None
    ) -> str

class MultiLLMClient:
    def __init__(self, registry=None)
    def add_client(name, client, is_default=False, provider=None)
    
    async def complete(
        prompt, system_prompt=None, client_name=None,
        agent_role=None, task_type=None, stream=False
    ) -> str
    
    async def complete_with_fallback(
        prompt, system_prompt=None, agent_role=None,
        task_type=None, max_retries=3
    ) -> str
```

---

## 完整示例

```python
import asyncio
import os
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.core.orchestrator import AgentOrchestrator, WorkflowType
from app.agents.base_agent import AgentRole
from app.config.agent_model_config import init_model_registry

async def main():
    # 1. 加载模型配置（可选）
    try:
        registry = init_model_registry("config/models_config.yaml")
    except ImportError:
        print("提示: 安装 pyyaml 以使用配置文件 pip install pyyaml")
        registry = None
    
    # 2. 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 3. 创建编排器
    orchestrator = AgentOrchestrator(llm_client, registry)
    
    # 4. 创建自定义Agent（使用不同模型）
    planner = orchestrator.create_agent(
        AgentRole.PLANNER,
        model_id="gpt-4"
    )
    writer = orchestrator.create_agent(
        AgentRole.WRITER,
        model_id="gpt-4"
    )
    editor = orchestrator.create_agent(
        AgentRole.STYLE_EDITOR,
        model_id="gpt-3.5-turbo"  # 简单任务用便宜的
    )
    
    # 5. 创建项目
    project = await orchestrator.create_novel_project(
        project_id="demo_project",
        title="AI协作小说",
        genre="科幻",
        user_input="一个关于人工智能觉醒的故事...",
        target_chapters=10
    )
    
    # 6. 撰写章节
    chapter = await orchestrator.write_chapter(
        project_id="demo_project",
        chapter_num=1
    )
    
    # 7. 获取统计
    stats = orchestrator.get_model_stats()
    print(f"使用的模型: {stats['model_usage']}")
    
    await llm_client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 最佳实践

1. **成本控制**
   - 简单任务（编辑润色）使用 `qwen-turbo` 或 `gpt-3.5-turbo`
   - 复杂任务（写作规划）使用 `qwen-plus` 或 `gpt-4`
   - 国产模型性价比更高

2. **可靠性**
   - 总是配置备用模型 (`fallback_models`)
   - 设置合理的重试次数

3. **性能优化**
   - 使用流式输出处理长文本
   - 缓存常用的世界设定和角色信息

4. **中文创作优化**
   - 使用 `qwen-plus` 或 `moonshot-v1-32k` 对中文支持更好
   - Kimi的超长上下文版本适合长篇小说

5. **模型选择建议**

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| 中文创意写作 | qwen-plus, moonshot-v1-32k | 中文支持优秀 |
| 英文创意写作 | gpt-4, claude-3-opus | 英文能力更强 |
| 情节规划 | qwen-plus, gpt-4 | 优秀的逻辑分析 |
| 内容润色 | qwen-turbo, gpt-3.5-turbo | 成本效益高 |
| 世界构建 | moonshot-v1-128k, qwen-long | 超长上下文 |
| 角色设计 | qwen-plus, gpt-4 | 细腻的描写能力 |
| 长篇小说 | moonshot-v1-128k, qwen-long | 超大上下文窗口 |

6. **国产模型推荐组合**

```yaml
# 高性价比组合（使用国产模型）
agent_models:
  planner: qwen-plus          # 通义千问Plus
  world_builder: moonshot-v1-128k  # Kimi超长上下文
  character_designer: qwen-plus
  writer: qwen-plus           # 中文写作效果好
  editor: qwen-turbo          # 快速便宜的润色

# 英文为主组合
agent_models:
  planner: gpt-4
  world_builder: claude-3-opus
  character_designer: gpt-4
  writer: gpt-4
  editor: gpt-3.5-turbo
```
