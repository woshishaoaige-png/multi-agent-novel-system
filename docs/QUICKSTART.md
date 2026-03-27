# 多Agent协作写小说系统 - 快速开始

## 1. 环境准备

### 1.1 安装Python依赖

```bash
cd /mnt/okcomputer/output/multi_agent_novel_system
pip install -r requirements.txt
```

### 1.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM API配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 可选：其他LLM提供商
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/novel_db

# 向量数据库
CHROMA_PERSIST_DIR=./data/chroma
```

## 2. 快速示例

### 2.1 创建作家风格

```python
import asyncio
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.services.style_service import StyleService

async def create_style():
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建风格服务
    style_service = StyleService()
    
    # 准备样本文本
    sample_texts = [
        """
        风清扬微微一笑，道："你倒也有趣。我这剑法，名为独孤九剑，
        乃是前辈高人独孤求败所创。这剑法讲究的是悟性，不是招式。"
        """,
        """
        令狐冲心中一凛，暗想："这位前辈剑法通神，我若能学得一二，
        也不枉了这次奇遇。"
        """
    ]
    
    # 分析风格
    style = await style_service.analyze_style(
        name="金庸武侠风格",
        sample_texts=sample_texts,
        llm_client=llm_client,
        description="金庸武侠小说的经典写作风格"
    )
    
    print(f"风格创建成功: {style.name}")
    print(f"词汇特征: {style.vocabulary_features}")
    
    await llm_client.close()

asyncio.run(create_style())
```

### 2.2 创建小说项目

```python
import asyncio
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.core.orchestrator import AgentOrchestrator

async def create_project():
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建项目
    result = await orchestrator.create_novel_project(
        project_id="my_first_novel",
        title="星际武侠传",
        genre="科幻武侠",
        user_input="""
        我想写一部科幻武侠小说，故事发生在未来的星际时代。
        主角是一个来自偏远星球的年轻人，偶然获得了一本古老的武学秘籍。
        他要在星际之间冒险，对抗邪恶的星际帝国。
        """,
        target_chapters=20
    )
    
    print(f"项目创建成功: {result['project_id']}")
    print(f"故事概要: {result['outline']['story_summary'][:200]}...")
    
    await llm_client.close()

asyncio.run(create_project())
```

### 2.3 撰写章节

```python
import asyncio
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.core.orchestrator import AgentOrchestrator

async def write_chapter():
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 假设项目已创建
    # 撰写第一章
    result = await orchestrator.write_chapter(
        project_id="my_first_novel",
        chapter_num=1,
        writer_style=None  # 或使用已创建的风格
    )
    
    print(f"章节撰写完成!")
    print(f"标题: {result['title']}")
    print(f"字数: {result['word_count']}")
    print(f"内容预览: {result['content'][:500]}...")
    
    await llm_client.close()

asyncio.run(write_chapter())
```

### 2.4 混合风格

```python
import asyncio
from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.services.style_service import StyleService

async def mix_styles():
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建风格服务
    style_service = StyleService()
    
    # 混合两种风格
    mixed_style = await style_service.mix_styles(
        style_names=["金庸武侠风格", "刘慈欣科幻风格"],
        mix_name="科幻武侠混合风格",
        proportions=[0.6, 0.4],
        llm_client=llm_client
    )
    
    print(f"混合风格创建成功: {mixed_style.name}")
    print(f"词汇特征: {mixed_style.vocabulary_features}")
    
    await llm_client.close()

asyncio.run(mix_styles())
```

## 3. 前端界面

### 3.1 启动前端开发服务器

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看界面

### 3.2 构建生产版本

```bash
cd frontend
npm run build
```

## 4. 项目结构

```
multi_agent_novel_system/
├── app/                          # 后端代码
│   ├── agents/                   # Agent实现
│   │   ├── base_agent.py         # Agent基类
│   │   ├── planner_agent.py      # 首席规划师
│   │   ├── writer_agent.py       # 主笔作家
│   │   ├── world_builder_agent.py # 世界构建师
│   │   ├── character_agent.py    # 角色设计师
│   │   └── editor_agent.py       # 风格编辑
│   ├── core/                     # 核心模块
│   │   └── orchestrator.py       # Agent编排器
│   └── services/                 # 服务层
│       ├── llm_client.py         # LLM客户端
│       └── style_service.py      # 风格服务
├── docs/                         # 文档
│   ├── ARCHITECTURE.md           # 架构设计
│   ├── API.md                    # API文档
│   └── QUICKSTART.md             # 快速开始
├── examples/                     # 示例代码
│   └── basic_usage.py            # 基础使用示例
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── App.tsx               # 主应用
│   │   └── components/           # UI组件
│   └── package.json
├── README.md                     # 项目说明
└── requirements.txt              # Python依赖
```

## 5. 核心概念

### 5.1 Agent

Agent是系统的核心执行单元，每个Agent有特定的角色和职责：

- **首席规划师 (Planner)**: 理解需求、生成大纲、协调Agent
- **世界构建师 (World Builder)**: 创建世界观、地理、历史
- **角色设计师 (Character Designer)**: 设计角色、关系网
- **主笔作家 (Writer)**: 撰写章节内容
- **风格编辑 (Editor)**: 润色内容、统一文风

### 5.2 作家风格

作家风格定义了AI写作的语言特征：

- **词汇特征**: 常用词汇类型、修辞手法
- **句式特点**: 长短句搭配、句式结构
- **叙事特征**: 叙事视角、节奏把控
- **对话风格**: 对话特点、语气
- **节奏风格**: 整体叙事节奏

### 5.3 协作模式

- **顺序协作**: Agent按顺序执行
- **并行协作**: 多个Agent同时工作
- **迭代协作**: 多轮优化直到质量达标

## 6. 常见问题

### Q: 如何添加新的Agent？

A: 继承BaseAgent类，实现execute方法，在Orchestrator中注册。

```python
from app.agents.base_agent import BaseAgent, AgentRole

class MyAgent(BaseAgent):
    def __init__(self, agent_id, llm_client):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.CUSTOM,
            name="我的Agent",
            description="自定义Agent",
            llm_client=llm_client
        )
    
    def get_system_prompt(self):
        return "系统提示词..."
    
    async def execute(self, task):
        # 实现任务逻辑
        return {"success": True}
```

### Q: 如何学习新的作家风格？

A: 使用StyleService.analyze_style方法：

```python
style = await style_service.analyze_style(
    name="新风格名称",
    sample_texts=["文本1", "文本2"],
    llm_client=llm_client
)
```

### Q: 如何混合多种风格？

A: 使用StyleService.mix_styles方法：

```python
mixed = await style_service.mix_styles(
    style_names=["风格1", "风格2"],
    mix_name="混合风格",
    proportions=[0.5, 0.5]
)
```

## 7. 下一步

- 阅读 [架构设计文档](ARCHITECTURE.md) 了解系统设计
- 阅读 [API文档](API.md) 了解接口详情
- 查看 [示例代码](../examples/basic_usage.py) 了解使用方式
- 参考 [MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel) 项目获取更多灵感
