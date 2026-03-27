# 多Agent协作写小说系统 - 架构设计文档

## 1. 系统概述

### 1.1 设计目标

本系统旨在构建一个智能化的多Agent协作小说创作平台，核心特性包括：

- **多Agent协作**: 多个专业Agent分工协作，完成从规划到写作的全流程
- **风格学习**: 支持学习用户喜欢的作家风格，塑造独特的AI作家
- **质量保障**: 生成-评估-优化闭环，确保内容质量
- **可扩展性**: 模块化设计，易于添加新的Agent和功能

### 1.2 参考项目

- **MuMuAINovel**: https://github.com/xiamuceer-j/MuMuAINovel
  - 借鉴其项目管理、角色管理、世界观设定等功能
  - 参考其前后端分离架构
  
- **CrewAI**: Role-based agent orchestration
  - 借鉴其角色定义和任务分配机制
  
- **AutoGen**: Conversational agent framework
  - 借鉴其Agent对话协作模式
  
- **Editor House**: https://github.com/Anubhob435/Ai-Agents-EditorHouse
  - 借鉴其多Agent书籍创作流程

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户交互层                              │
│  - Web界面 (React + TypeScript)                             │
│  - API接口 (FastAPI)                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      编排协调层 (Orchestrator)                │
│  - 任务调度器 (Task Scheduler)                              │
│  - Agent协调器 (Agent Coordinator)                          │
│  - 状态管理器 (State Manager)                               │
│  - 质量监控器 (Quality Monitor)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Agent协作层                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │规划师  │ │世界    │ │角色    │ │作家    │ │编辑    │    │
│  │(P)     │ │(W)     │ │(C)     │ │(Wr)    │ │(E)     │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    作家风格系统 (Style System)                │
│  - 风格分析器 (Style Analyzer)                              │
│  - 风格存储库 (Style Repository)                            │
│  - 风格迁移模块 (Style Transfer)                            │
│  - 风格混合器 (Style Mixer)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         基础设施层                            │
│  - LLM接口 (OpenAI/Claude/Gemini)                          │
│  - 向量数据库 (ChromaDB)                                    │
│  - 关系数据库 (PostgreSQL)                                  │
│  - 缓存系统 (Redis)                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Agent角色定义

| Agent | 职责 | 关键能力 |
|-------|------|----------|
| **首席规划师 (Planner)** | 理解需求、生成大纲、协调Agent | 需求分析、任务分解、项目管理 |
| **世界构建师 (World Builder)** | 创建世界观、地理、历史 | 世界设定、文化构建、规则设计 |
| **角色设计师 (Character Designer)** | 设计角色、关系网 | 人物刻画、心理描写、成长弧线 |
| **情节策划师 (Plot Planner)** | 设计情节、冲突、转折 | 情节设计、悬念设置、节奏把控 |
| **主笔作家 (Lead Writer)** | 撰写章节内容 | 场景描写、对话设计、叙事技巧 |
| **风格编辑 (Style Editor)** | 润色内容、统一文风 | 语言润色、风格统一、修辞优化 |
| **审核员 (Reviewer)** | 质量检查、一致性验证 | 逻辑检查、质量评估、问题发现 |

### 2.3 协作模式

#### 2.3.1 顺序协作
```
用户输入 → Planner → World Builder → Character Designer → Writer → Editor → Reviewer → 输出
```

#### 2.3.2 并行协作
```
                ┌→ World Builder ─┐
Planner ────────┼→ Character Designer ─┼→ Writer → Editor → Reviewer
                └→ Plot Planner ──────┘
```

#### 2.3.3 迭代协作
```
Writer → Editor → Reviewer ─┐
     ↑                        │
     └────────────────────────┘ (循环直到质量达标)
```

## 3. 核心模块设计

### 3.1 Agent基类 (BaseAgent)

```python
class BaseAgent(ABC):
    - agent_id: str
    - role: AgentRole
    - name: str
    - description: str
    - llm_client: LLMClient
    - style: Optional[WriterStyle]
    - memory: AgentMemory
    
    + execute(task: Dict) -> Dict
    + think(context: Dict) -> Dict
    + collaborate(target: BaseAgent, message: Dict) -> Dict
    + review(content: Dict) -> Dict
```

### 3.2 编排协调器 (AgentOrchestrator)

```python
class AgentOrchestrator:
    - agents: Dict[str, BaseAgent]
    - workflows: Dict[str, Workflow]
    - projects: Dict[str, Project]
    
    + register_agent(agent: BaseAgent)
    + create_workflow(config: WorkflowConfig) -> Workflow
    + execute_workflow(workflow_id: str) -> Dict
    + create_novel_project(config: ProjectConfig) -> Project
    + write_chapter(project_id: str, chapter_num: int) -> Dict
```

### 3.3 风格学习系统 (StyleService)

```python
class StyleService:
    - styles: Dict[str, WriterStyle]
    - storage_path: Path
    
    + analyze_style(name: str, sample_texts: List[str]) -> WriterStyle
    + get_style(name: str) -> WriterStyle
    + mix_styles(names: List[str], proportions: List[float]) -> WriterStyle
    + delete_style(name: str)
```

## 4. 数据模型

### 4.1 项目 (Project)

```python
@dataclass
class Project:
    project_id: str
    title: str
    genre: str
    outline: Dict
    world: Dict
    characters: Dict[str, Character]
    chapters: Dict[str, Chapter]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
```

### 4.2 章节 (Chapter)

```python
@dataclass
class Chapter:
    chapter_num: int
    title: str
    content: str
    word_count: int
    status: ChapterStatus
    outline: Dict
    versions: List[ChapterVersion]
    reviews: List[Review]
```

### 4.3 作家风格 (WriterStyle)

```python
@dataclass
class WriterStyle:
    name: str
    description: str
    vocabulary_features: List[str]
    sentence_patterns: List[str]
    narrative_features: List[str]
    dialogue_style: str
    pacing_style: str
    system_prompt: str
    sample_texts: List[str]
```

## 5. 工作流程

### 5.1 项目创建流程

```
1. 用户输入创作需求
2. 首席规划师分析需求
3. 生成故事大纲
4. 世界构建师创建世界观
5. 角色设计师创建主要角色
6. 保存项目信息
7. 返回项目概览
```

### 5.2 章节写作流程

```
1. 首席规划师协调上下文
2. 获取世界观信息
3. 获取角色信息
4. 获取情节指导
5. 主笔作家撰写初稿
6. 风格编辑润色
7. 审核员质量检查
8. 如未通过，返回修改
9. 保存最终版本
```

### 5.3 风格学习流程

```
1. 用户上传作家样本文本
2. 风格分析器提取特征
   - 词汇特征
   - 句式特点
   - 叙事特征
   - 对话风格
   - 节奏风格
3. 生成系统提示词
4. 保存风格模板
5. 可用于创建作家Agent
```

## 6. 技术选型

### 6.1 后端技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web框架 | FastAPI | 高性能异步API框架 |
| 数据库 | PostgreSQL | 关系型数据存储 |
| ORM | SQLAlchemy | 数据库操作 |
| 向量数据库 | ChromaDB | 风格向量存储 |
| 缓存 | Redis | 会话和状态缓存 |
| LLM客户端 | 多提供商 | OpenAI, Claude, Gemini |

### 6.2 前端技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | React 18 | UI框架 |
| 语言 | TypeScript | 类型安全 |
| 样式 | Tailwind CSS | 原子化CSS |
| 组件库 | shadcn/ui | UI组件 |
| 状态管理 | React Context | 状态管理 |

## 7. 扩展性设计

### 7.1 添加新Agent

1. 继承BaseAgent基类
2. 实现execute方法
3. 定义系统提示词
4. 在Orchestrator中注册

### 7.2 添加新风格

1. 准备样本文本
2. 调用StyleService.analyze_style
3. 保存风格模板
4. 创建对应WriterAgent

### 7.3 自定义工作流

1. 定义任务序列
2. 指定Agent分配
3. 设置依赖关系
4. 执行工作流

## 8. 性能优化

### 8.1 LLM调用优化

- 使用流式输出
- 实现请求缓存
- 批量处理
- 异步并发

### 8.2 存储优化

- 向量索引
- 数据库连接池
- 缓存策略
- 增量更新

## 9. 安全考虑

- API Key管理
- 用户认证授权
- 输入验证
- 内容过滤
- 访问控制

## 10. 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      负载均衡器                          │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   API服务器1     │ │   API服务器2     │ │   API服务器N     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    数据库集群                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ PostgreSQL  │  │    Redis    │  │    ChromaDB     │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 11. 未来规划

### 11.1 功能扩展

- [ ] 支持更多LLM提供商
- [ ] 添加图片生成功能
- [ ] 支持多语言创作
- [ ] 添加协作编辑功能
- [ ] 支持导出更多格式

### 11.2 性能提升

- [ ] 实现分布式Agent调度
- [ ] 优化LLM调用效率
- [ ] 添加增量生成支持
- [ ] 实现智能缓存策略

## 12. 总结

本系统通过多Agent协作和风格学习，实现了智能化的小说创作辅助。模块化设计保证了系统的可扩展性，生成-评估-优化闭环确保了内容质量。
