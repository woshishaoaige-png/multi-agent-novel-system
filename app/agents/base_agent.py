"""
多Agent协作写小说系统 - Agent基类

参考架构:
- MuMuAINovel: https://github.com/xiamuceer-j/MuMuAINovel
- CrewAI: Role-based agent orchestration
- AutoGen: Conversational agent framework
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from datetime import datetime

# 类型检查时导入，避免循环依赖
if TYPE_CHECKING:
    from ..config.agent_model_config import ModelInfo


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    REVIEWING = "reviewing"
    WAITING = "waiting"
    ERROR = "error"


class AgentRole(Enum):
    """Agent角色类型"""
    PLANNER = "planner"           # 首席规划师
    WORLD_BUILDER = "world_builder"  # 世界构建师
    CHARACTER_DESIGNER = "character_designer"  # 角色设计师
    PLOT_PLANNER = "plot_planner"  # 情节策划师
    WRITER = "writer"             # 主笔作家
    STYLE_EDITOR = "style_editor"  # 风格编辑
    REVIEWER = "reviewer"         # 审核员
    FORESHADOW = "foreshadow"     # 伏笔管理
    DIALOGUE = "dialogue"         # 对话优化
    CONSISTENCY = "consistency"   # 一致性检查


@dataclass
class AgentMessage:
    """Agent间消息"""
    from_agent: str
    to_agent: str
    message_type: str  # request, response, feedback, notification
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Agent记忆"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)  # 短期记忆
    long_term: Dict[str, Any] = field(default_factory=dict)         # 长期记忆
    context_window: int = 10  # 上下文窗口大小
    
    def add_to_short_term(self, item: Dict[str, Any]):
        """添加到短期记忆"""
        self.short_term.append(item)
        if len(self.short_term) > self.context_window:
            self.short_term.pop(0)
    
    def get_context(self) -> str:
        """获取上下文"""
        return json.dumps(self.short_term[-self.context_window:], ensure_ascii=False, indent=2)


@dataclass
class WriterStyle:
    """作家风格定义"""
    name: str
    description: str
    vocabulary_features: List[str] = field(default_factory=list)
    sentence_patterns: List[str] = field(default_factory=list)
    narrative_features: List[str] = field(default_factory=list)
    dialogue_style: str = ""
    pacing_style: str = ""
    system_prompt: str = ""
    sample_texts: List[str] = field(default_factory=list)
    
    def to_prompt(self) -> str:
        """转换为系统提示词"""
        return f"""你是一位具有独特写作风格的作家，你的风格特点如下：

【风格名称】{self.name}
【风格描述】{self.description}

【词汇特征】
{chr(10).join(f"- {f}" for f in self.vocabulary_features)}

【句式特点】
{chr(10).join(f"- {p}" for p in self.sentence_patterns)}

【叙事特征】
{chr(10).join(f"- {n}" for n in self.narrative_features)}

【对话风格】{self.dialogue_style}

【节奏风格】{self.pacing_style}

{self.system_prompt}
"""


class BaseAgent(ABC):
    """
    Agent基类
    
    所有专业Agent的基类，提供：
    - 状态管理
    - 记忆管理
    - 消息通信
    - LLM交互
    - 模型选择支持
    """
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        name: str,
        description: str,
        llm_client: Any,
        style: Optional[WriterStyle] = None,
        tools: Optional[List[Callable]] = None,
        model_id: Optional[str] = None,
        model_info: Optional["ModelInfo"] = None
    ):
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.style = style
        self.tools = tools or []
        
        # 模型配置
        self.model_id: Optional[str] = model_id  # 当前使用的模型ID
        self.model_info: Optional["ModelInfo"] = model_info  # 模型信息
        
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.collaborators: Dict[str, 'BaseAgent'] = {}
        
        # 性能统计
        self.stats = {
            "tasks_completed": 0,
            "tokens_consumed": 0,
            "total_time": 0.0,
            "model_calls": {}  # 记录各模型的调用次数
        }
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体任务，子类必须实现"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词，子类必须实现"""
        pass
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        思考阶段 - 分析任务并制定执行计划
        
        Args:
            context: 任务上下文
            
        Returns:
            执行计划
        """
        self.status = AgentStatus.THINKING
        
        prompt = f"""作为{self.name}，请分析以下任务并制定执行计划：

【任务描述】
{context.get('task_description', '无')}

【已有信息】
{json.dumps(context.get('existing_info', {}), ensure_ascii=False, indent=2)}

【历史上下文】
{self.memory.get_context()}

请输出：
1. 任务理解
2. 执行步骤
3. 需要协作的Agent
4. 预期输出格式
"""
        
        response = await self._call_llm(prompt)
        
        return {
            "plan": response,
            "agent": self.agent_id,
            "role": self.role.value
        }
    
    async def collaborate(
        self,
        target_agent: 'BaseAgent',
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        与其他Agent协作
        
        Args:
            target_agent: 目标Agent
            message: 协作消息
            
        Returns:
            协作结果
        """
        self.status = AgentStatus.WAITING
        
        agent_message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=target_agent.agent_id,
            message_type="request",
            content=message
        )
        
        # 发送消息
        await target_agent.receive_message(agent_message)
        
        # 等待响应
        response = await self.wait_for_response(target_agent.agent_id)
        
        return response
    
    async def receive_message(self, message: AgentMessage):
        """接收消息"""
        await self.message_queue.put(message)
    
    async def wait_for_response(
        self,
        from_agent_id: str,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """等待特定Agent的响应"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"等待 {from_agent_id} 响应超时")
            
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                if message.from_agent == from_agent_id:
                    return message.content
            except asyncio.TimeoutError:
                continue
    
    async def review(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        审核内容（可选实现）
        
        Args:
            content: 待审核内容
            
        Returns:
            审核结果
        """
        self.status = AgentStatus.REVIEWING
        
        prompt = f"""作为{self.name}，请审核以下内容：

【待审核内容】
{json.dumps(content, ensure_ascii=False, indent=2)}

请从以下维度进行评估：
1. 内容质量
2. 逻辑一致性
3. 风格统一性
4. 改进建议

输出格式：JSON
{{
    "score": 0-100,
    "quality_assessment": "质量评估",
    "consistency_check": "一致性检查",
    "style_evaluation": "风格评估",
    "suggestions": ["建议1", "建议2"],
    "approved": true/false
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "score": 70,
                "quality_assessment": response,
                "approved": True
            }
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        调用LLM
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            stream: 是否流式输出
            model_id: 指定使用的模型（可选）
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        if system_prompt is None:
            system_prompt = self.get_system_prompt()
        
        # 如果有作家风格，追加到系统提示词
        if self.style:
            system_prompt = f"{system_prompt}\n\n{self.style.to_prompt()}"
        
        # 确定要使用的模型
        effective_model = model_id or self.model_id
        
        # 记录模型使用
        if effective_model:
            if effective_model not in self.stats["model_calls"]:
                self.stats["model_calls"][effective_model] = 0
            self.stats["model_calls"][effective_model] += 1
        
        # 调用LLM客户端
        response = await self.llm_client.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            stream=stream,
            model=effective_model,
            agent_role=self.role.value,  # 传递Agent角色用于模型选择
            **kwargs
        )
        
        # 更新统计
        self.stats["tokens_consumed"] += len(prompt) + len(response)
        
        return response
    
    def update_memory(self, key: str, value: Any):
        """更新长期记忆"""
        self.memory.long_term[key] = value
    
    def get_memory(self, key: str) -> Any:
        """获取长期记忆"""
        return self.memory.long_term.get(key)
    
    def add_collaborator(self, agent: 'BaseAgent'):
        """添加协作者"""
        self.collaborators[agent.agent_id] = agent
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "stats": self.stats,
            "model_id": self.model_id,
            "model_info": {
                "provider": self.model_info.provider if self.model_info else None,
                "model_name": self.model_info.model_name if self.model_info else None
            } if self.model_info else None,
            "collaborators": list(self.collaborators.keys())
        }
    
    def switch_model(self, model_id: str):
        """
        切换Agent使用的模型
        
        Args:
            model_id: 新的模型ID
        """
        self.model_id = model_id
        # 可以在这里添加模型切换的日志或通知
    
    async def reset(self):
        """重置Agent状态"""
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self.stats = {
            "tasks_completed": 0,
            "tokens_consumed": 0,
            "total_time": 0.0,
            "model_calls": {}
        }
