"""
Agent编排协调器 (Orchestrator)

多Agent系统的核心，负责：
- Agent生命周期管理
- 任务调度
- 工作流编排
- 状态管理
- 质量监控
- Agent级别模型配置
"""

from typing import Dict, List, Any, Optional, Type, Union
import asyncio
import json
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..agents.base_agent import BaseAgent, AgentRole, AgentStatus
from ..agents.planner_agent import PlannerAgent
from ..agents.writer_agent import WriterAgent
from ..agents.world_builder_agent import WorldBuilderAgent
from ..agents.character_agent import CharacterAgent
from ..agents.editor_agent import EditorAgent
from ..config.agent_model_config import (
    AgentModelRegistry,
    AgentModelConfig,
    get_model_registry,
    ModelInfo,
    ModelCapability
)


class WorkflowType(Enum):
    """工作流类型"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    ITERATIVE = "iterative"        # 迭代执行
    HYBRID = "hybrid"              # 混合执行


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    agent_id: str
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    # 新增：指定任务使用的模型
    model_id: Optional[str] = None


@dataclass
class Workflow:
    """工作流定义"""
    workflow_id: str
    name: str
    type: WorkflowType
    tasks: List[Task]
    project_id: str
    status: TaskStatus = TaskStatus.PENDING
    current_task_idx: int = 0
    iterations: int = 0
    max_iterations: int = 3


class AgentOrchestrator:
    """
    Agent编排协调器
    
    参考架构：
    - CrewAI: Role-based orchestration
    - LangGraph: Graph-based workflow
    - AutoGen: Conversational coordination
    
    新增功能：
    - 支持Agent级别的大模型配置
    - 支持任务级别的模型选择
    - 支持模型回退机制
    """
    
    def __init__(
        self, 
        llm_client: Any,
        model_registry: Optional[AgentModelRegistry] = None
    ):
        self.llm_client = llm_client
        
        # 模型注册表
        self.model_registry = model_registry or get_model_registry()
        
        # Agent注册表
        self.agents: Dict[str, BaseAgent] = {}
        
        # Agent模型配置映射 {agent_id: model_id}
        self.agent_models: Dict[str, str] = {}
        
        # 工作流管理
        self.workflows: Dict[str, Workflow] = {}
        
        # 项目管理
        self.projects: Dict[str, Dict[str, Any]] = {}
        
        # 事件监听
        self.event_listeners: List[callable] = []
        
        # 运行状态
        self.is_running = False
    
    def register_agent(self, agent: BaseAgent) -> str:
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        
        # 获取Agent的模型配置
        agent_role = agent.role.value
        model_config = self.model_registry.get_agent_config(agent_role)
        
        if model_config:
            self.agent_models[agent.agent_id] = model_config.primary_model
            # 设置Agent的LLM客户端配置
            self._configure_agent_llm(agent, model_config)
        
        # 通知其他Agent
        for other_agent in self.agents.values():
            if other_agent.agent_id != agent.agent_id:
                other_agent.add_collaborator(agent)
        
        return agent.agent_id
    
    def _configure_agent_llm(self, agent: BaseAgent, config: AgentModelConfig):
        """
        配置Agent的LLM
        
        根据Agent的模型配置，设置LLM客户端的默认参数
        """
        model_info = self.model_registry.get_model(config.primary_model)
        if model_info:
            # 更新Agent的模型信息
            agent.model_id = config.primary_model
            agent.model_info = model_info
    
    def create_agent(
        self,
        role: AgentRole,
        agent_id: Optional[str] = None,
        style: Optional[Any] = None,
        model_id: Optional[str] = None
    ) -> BaseAgent:
        """
        创建并注册Agent
        
        Args:
            role: Agent角色
            agent_id: Agent ID（可选）
            style: 作家风格（可选）
            model_id: 指定使用的模型ID（可选，默认使用角色配置）
        """
        if agent_id is None:
            agent_id = f"{role.value}_{len(self.agents)}"
        
        agent_classes = {
            AgentRole.PLANNER: PlannerAgent,
            AgentRole.WRITER: WriterAgent,
            AgentRole.WORLD_BUILDER: WorldBuilderAgent,
            AgentRole.CHARACTER_DESIGNER: CharacterAgent,
            AgentRole.STYLE_EDITOR: EditorAgent,
        }
        
        agent_class = agent_classes.get(role)
        if agent_class is None:
            raise ValueError(f"未知的Agent角色: {role}")
        
        # 获取Agent的模型配置
        model_to_use = model_id
        if model_to_use is None:
            model_config = self.model_registry.get_agent_config(role.value)
            if model_config:
                model_to_use = model_config.primary_model
        
        # 创建Agent
        agent = agent_class(
            agent_id=agent_id,
            llm_client=self.llm_client,
            style=style
        )
        
        # 设置模型信息
        if model_to_use:
            agent.model_id = model_to_use
            model_info = self.model_registry.get_model(model_to_use)
            if model_info:
                agent.model_info = model_info
        
        self.register_agent(agent)
        return agent
    
    def set_agent_model(self, agent_id: str, model_id: str):
        """
        为特定Agent设置使用的模型
        
        Args:
            agent_id: Agent ID
            model_id: 模型ID
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent不存在: {agent_id}")
        
        self.agent_models[agent_id] = model_id
        self.agents[agent_id].model_id = model_id
        self.agents[agent_id].model_info = self.model_registry.get_model(model_id)
    
    def get_agent_model(self, agent_id: str) -> Optional[str]:
        """获取Agent当前使用的模型"""
        return self.agent_models.get(agent_id)
    
    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        workflow_type: WorkflowType,
        project_id: str,
        tasks_config: List[Dict[str, Any]]
    ) -> Workflow:
        """创建工作流"""
        tasks = []
        for i, config in enumerate(tasks_config):
            task = Task(
                task_id=f"{workflow_id}_task_{i}",
                task_type=config["type"],
                agent_id=config["agent_id"],
                params=config.get("params", {}),
                dependencies=config.get("dependencies", []),
                model_id=config.get("model_id")  # 支持任务级别模型配置
            )
            tasks.append(task)
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            type=workflow_type,
            tasks=tasks,
            project_id=project_id
        )
        
        self.workflows[workflow_id] = workflow
        return workflow
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """执行工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow.status = TaskStatus.RUNNING
        self._emit_event("workflow_started", {"workflow_id": workflow_id})
        
        try:
            if workflow.type == WorkflowType.SEQUENTIAL:
                result = await self._execute_sequential(workflow)
            elif workflow.type == WorkflowType.PARALLEL:
                result = await self._execute_parallel(workflow)
            elif workflow.type == WorkflowType.ITERATIVE:
                result = await self._execute_iterative(workflow)
            elif workflow.type == WorkflowType.HYBRID:
                result = await self._execute_hybrid(workflow)
            else:
                raise ValueError(f"未知的工作流类型: {workflow.type}")
            
            workflow.status = TaskStatus.COMPLETED
            self._emit_event("workflow_completed", {"workflow_id": workflow_id, "result": result})
            
            return result
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            self._emit_event("workflow_failed", {"workflow_id": workflow_id, "error": str(e)})
            raise
    
    async def _execute_sequential(self, workflow: Workflow) -> Dict[str, Any]:
        """顺序执行工作流"""
        results = []
        
        for task in workflow.tasks:
            # 检查依赖
            for dep_id in task.dependencies:
                dep_task = next((t for t in workflow.tasks if t.task_id == dep_id), None)
                if dep_task and dep_task.status != TaskStatus.COMPLETED:
                    raise ValueError(f"任务 {task.task_id} 的依赖 {dep_id} 未完成")
            
            # 执行任务
            result = await self._execute_task(task)
            results.append(result)
        
        return {
            "workflow_id": workflow.workflow_id,
            "results": results
        }
    
    async def _execute_parallel(self, workflow: Workflow) -> Dict[str, Any]:
        """并行执行工作流"""
        # 按依赖分组
        dependency_groups = self._group_by_dependencies(workflow.tasks)
        
        all_results = []
        for group in dependency_groups:
            # 并行执行组内任务
            tasks = [self._execute_task(task) for task in group]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(results)
        
        return {
            "workflow_id": workflow.workflow_id,
            "results": all_results
        }
    
    async def _execute_iterative(self, workflow: Workflow) -> Dict[str, Any]:
        """迭代执行工作流"""
        iteration = 0
        
        while iteration < workflow.max_iterations:
            workflow.iterations = iteration
            
            # 执行一轮
            results = []
            for task in workflow.tasks:
                result = await self._execute_task(task)
                results.append(result)
            
            # 检查是否满足终止条件
            if self._check_termination(results):
                break
            
            iteration += 1
        
        return {
            "workflow_id": workflow.workflow_id,
            "iterations": iteration + 1,
            "results": results
        }
    
    async def _execute_hybrid(self, workflow: Workflow) -> Dict[str, Any]:
        """混合执行工作流"""
        return await self._execute_sequential(workflow)
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """执行单个任务"""
        agent = self.agents.get(task.agent_id)
        if not agent:
            raise ValueError(f"Agent不存在: {task.agent_id}")
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        # 获取要使用的模型
        model_to_use = task.model_id or self.agent_models.get(task.agent_id)
        
        self._emit_event("task_started", {
            "task_id": task.task_id, 
            "agent_id": task.agent_id,
            "model": model_to_use
        })
        
        try:
            # 带有模型选择的执行
            result = await self._execute_task_with_model(agent, task.params, model_to_use)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.end_time = datetime.now()
            
            self._emit_event("task_completed", {
                "task_id": task.task_id, 
                "result": result,
                "model_used": model_to_use
            })
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            
            # 尝试使用备用模型
            if model_to_use:
                try:
                    fallback_result = await self._try_fallback_model(agent, task)
                    if fallback_result:
                        task.status = TaskStatus.COMPLETED
                        task.result = fallback_result
                        self._emit_event("task_completed_with_fallback", {
                            "task_id": task.task_id,
                            "original_model": model_to_use,
                            "fallback_model": task.result.get("_fallback_model"),
                            "result": fallback_result
                        })
                        return fallback_result
                except:
                    pass
            
            self._emit_event("task_failed", {"task_id": task.task_id, "error": str(e)})
            raise
    
    async def _execute_task_with_model(
        self, 
        agent: BaseAgent, 
        params: Dict[str, Any],
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用指定模型执行任务"""
        # 如果指定了模型，临时修改agent的模型配置
        original_model_id = getattr(agent, 'model_id', None)
        original_model_info = getattr(agent, 'model_info', None)
        
        if model_id:
            agent.model_id = model_id
            agent.model_info = self.model_registry.get_model(model_id)
        
        try:
            result = await agent.execute(params)
            result["_model_used"] = model_id or original_model_id
            return result
        finally:
            # 恢复原始配置
            if original_model_id:
                agent.model_id = original_model_id
            if original_model_info:
                agent.model_info = original_model_info
    
    async def _try_fallback_model(
        self, 
        agent: BaseAgent, 
        task: Task
    ) -> Optional[Dict[str, Any]]:
        """尝试使用备用模型"""
        agent_config = self.model_registry.get_agent_config(agent.role.value)
        if not agent_config or not agent_config.fallback_models:
            return None
        
        for fallback_model in agent_config.fallback_models:
            try:
                result = await self._execute_task_with_model(agent, task.params, fallback_model)
                result["_fallback_model"] = fallback_model
                return result
            except Exception:
                continue
        
        return None
    
    def _group_by_dependencies(self, tasks: List[Task]) -> List[List[Task]]:
        """按依赖关系分组"""
        return [tasks]
    
    def _check_termination(self, results: List[Dict[str, Any]]) -> bool:
        """检查是否满足终止条件"""
        return all(r.get("success", False) for r in results if isinstance(r, dict))
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """发送事件"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception:
                pass
    
    def add_event_listener(self, listener: callable):
        """添加事件监听"""
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: callable):
        """移除事件监听"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    # ==================== 便捷方法 ====================
    
    async def create_novel_project(
        self,
        project_id: str,
        title: str,
        genre: str,
        user_input: str,
        target_chapters: int = 20,
        agent_models: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        创建小说项目
        
        Args:
            project_id: 项目ID
            title: 标题
            genre: 类型
            user_input: 用户输入
            target_chapters: 目标章节数
            agent_models: Agent到模型的映射 {"planner": "gpt-4", "writer": "claude-3-opus"}
        """
        # 创建Agent（支持自定义模型）
        planner = self.create_agent(
            AgentRole.PLANNER, 
            f"{project_id}_planner",
            model_id=agent_models.get("planner") if agent_models else None
        )
        world_builder = self.create_agent(
            AgentRole.WORLD_BUILDER, 
            f"{project_id}_world",
            model_id=agent_models.get("world_builder") if agent_models else None
        )
        character_designer = self.create_agent(
            AgentRole.CHARACTER_DESIGNER, 
            f"{project_id}_char",
            model_id=agent_models.get("character_designer") if agent_models else None
        )
        
        # 创建规划工作流
        planning_workflow = self.create_workflow(
            workflow_id=f"{project_id}_planning",
            name="项目规划",
            workflow_type=WorkflowType.SEQUENTIAL,
            project_id=project_id,
            tasks_config=[
                {
                    "type": "create_outline",
                    "agent_id": planner.agent_id,
                    "params": {
                        "type": "create_outline",
                        "user_input": user_input,
                        "genre": genre,
                        "target_chapters": target_chapters
                    },
                    "model_id": agent_models.get("planner") if agent_models else None
                },
                {
                    "type": "create_world",
                    "agent_id": world_builder.agent_id,
                    "params": {
                        "type": "create_world",
                        "genre": genre
                    },
                    "dependencies": [f"{project_id}_planning_task_0"],
                    "model_id": agent_models.get("world_builder") if agent_models else None
                }
            ]
        )
        
        # 执行规划
        result = await self.execute_workflow(planning_workflow.workflow_id)
        
        # 保存项目信息
        self.projects[project_id] = {
            "project_id": project_id,
            "title": title,
            "genre": genre,
            "outline": result.get("results", [{}])[0].get("outline", {}),
            "world": result.get("results", [{}])[1].get("world", {}),
            "agents": [planner.agent_id, world_builder.agent_id, character_designer.agent_id],
            "agent_models": agent_models or {},
            "chapters": {},
            "status": "planning_completed"
        }
        
        return {
            "success": True,
            "project_id": project_id,
            "outline": self.projects[project_id]["outline"],
            "world": self.projects[project_id]["world"],
            "agent_models_used": agent_models or self._get_default_agent_models()
        }
    
    async def write_chapter(
        self,
        project_id: str,
        chapter_num: int,
        writer_style: Optional[Any] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撰写章节
        
        Args:
            project_id: 项目ID
            chapter_num: 章节号
            writer_style: 作家风格
            model_id: 指定使用的模型（可选）
        """
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 获取默认模型或使用指定的模型
        default_model = project.get("agent_models", {}).get("writer")
        writer_model = model_id or default_model or self.agent_models.get(f"{project_id}_writer_1")
        
        # 创建或获取Writer Agent
        writer_id = f"{project_id}_writer_{chapter_num}"
        if writer_id not in self.agents:
            writer = self.create_agent(
                AgentRole.WRITER, 
                writer_id, 
                style=writer_style,
                model_id=writer_model
            )
        else:
            writer = self.agents[writer_id]
            if writer_model:
                self.set_agent_model(writer_id, writer_model)
        
        # 获取规划师协调上下文
        planner = self.agents.get(f"{project_id}_planner")
        if planner:
            coordination = await planner.coordinate_writing(
                chapter_num=chapter_num,
                collaborators={
                    "world_builder": self.agents.get(f"{project_id}_world"),
                    "character_designer": self.agents.get(f"{project_id}_char")
                }
            )
        else:
            coordination = {"writer_input": {}}
        
        # 执行写作
        result = await self._execute_task_with_model(
            writer, 
            {
                "type": "write_chapter",
                "chapter_num": chapter_num,
                **coordination.get("writer_input", {})
            },
            writer_model
        )
        
        # 保存章节
        project["chapters"][str(chapter_num)] = {
            "chapter_num": chapter_num,
            "content": result.get("content", ""),
            "word_count": result.get("word_count", 0),
            "model_used": writer_model,
            "status": "written"
        }
        
        return result
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """获取项目状态"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "项目不存在"}
        
        return {
            "project_id": project_id,
            "title": project["title"],
            "status": project["status"],
            "total_chapters": len(project.get("outline", {}).get("chapters", [])),
            "completed_chapters": len(project.get("chapters", {})),
            "agents": [
                {
                    **self.agents[aid].get_status(),
                    "model": self.agent_models.get(aid, "default")
                }
                for aid in project["agents"] 
                if aid in self.agents
            ],
            "agent_models": project.get("agent_models", {})
        }
    
    def _get_default_agent_models(self) -> Dict[str, str]:
        """获取默认Agent模型映射"""
        models = {}
        for role, config in self.model_registry.agent_configs.items():
            models[role] = config.primary_model
        return models
    
    def get_model_stats(self) -> Dict[str, Any]:
        """获取模型使用统计"""
        model_usage = {}
        for agent_id, model_id in self.agent_models.items():
            if model_id not in model_usage:
                model_usage[model_id] = []
            model_usage[model_id].append(agent_id)
        
        return {
            "total_agents": len(self.agents),
            "model_usage": model_usage,
            "available_models": self.model_registry.list_models()
        }
