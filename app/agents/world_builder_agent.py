"""
世界构建师 Agent

负责：
- 创建小说世界观
- 设计地理、历史、文化
- 维护世界设定的一致性
"""

from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent, AgentRole


class WorldBuilderAgent(BaseAgent):
    """
    世界构建师 Agent
    
    参考MuMuAINovel的世界观设定功能
    """
    
    def __init__(self, agent_id: str, llm_client: Any, style: Optional[Any] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.WORLD_BUILDER,
            name="世界构建师",
            description="负责创建和维护小说世界观",
            llm_client=llm_client,
            style=style
        )
        
        # 世界设定存储
        self.world_settings: Dict[str, Any] = {}
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的世界构建师，擅长创造引人入胜的虚构世界。

你的职责：
1. 设计完整的世界观体系
2. 创建地理、历史、文化背景
3. 设计魔法/科技系统（如需要）
4. 维护世界设定的一致性

设计原则：
- 内部逻辑自洽
- 细节丰富但不冗余
- 为故事服务
- 留有创作空间

输出要求：
- 结构化数据
- 便于查询和引用
- 支持增量更新
"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行世界构建任务
        
        Args:
            task: {
                "type": "create_world" | "update_world" | "get_context",
                "genre": str,
                "requirements": Dict,
                "existing_world": Optional[Dict]
            }
        """
        task_type = task.get("type", "create_world")
        
        if task_type == "create_world":
            return await self._create_world(task)
        elif task_type == "update_world":
            return await self._update_world(task)
        elif task_type == "get_context":
            return await self._get_context(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
    
    async def _create_world(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """创建世界观"""
        genre = task.get("genre", "fantasy")
        requirements = task.get("requirements", {})
        
        prompt = f"""请为{type}类型小说创建完整的世界观设定。

【小说类型】{genre}
【特殊要求】
{json.dumps(requirements, ensure_ascii=False, indent=2)}

请输出完整的世界观设定，包含以下模块：

1. **基本信息**
   - 世界名称
   - 时代背景
   - 整体氛围

2. **地理环境**
   - 大陆/星球概况
   - 主要地区/国家
   - 重要地点
   - 气候特征

3. **历史背景**
   - 创世神话/起源
   - 重要历史时期
   - 当前时代背景

4. **社会文化**
   - 政治体系
   - 社会阶层
   - 宗教信仰
   - 风俗习惯
   - 语言特点

5. **特殊系统**（根据类型选择）
   - 魔法系统 / 科技系统
   - 力量等级体系
   - 特殊规则

6. **势力组织**
   - 主要势力
   - 组织关系
   - 冲突背景

7. **世界规则**
   - 物理规则
   - 社会规则
   - 特殊限制

输出格式：JSON
{{
    "basic_info": {{...}},
    "geography": {{...}},
    "history": {{...}},
    "culture": {{...}},
    "special_system": {{...}},
    "factions": {{...}},
    "rules": {{...}}
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            world = json.loads(response)
        except json.JSONDecodeError:
            world = {"raw_world": response}
        
        self.world_settings = world
        self.update_memory("world_settings", world)
        
        return {
            "success": True,
            "world": world,
            "agent": self.agent_id
        }
    
    async def _update_world(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """更新世界观"""
        updates = task.get("updates", {})
        
        # 更新世界设定
        for key, value in updates.items():
            if key in self.world_settings:
                if isinstance(value, dict) and isinstance(self.world_settings[key], dict):
                    self.world_settings[key].update(value)
                else:
                    self.world_settings[key] = value
            else:
                self.world_settings[key] = value
        
        self.update_memory("world_settings", self.world_settings)
        
        return {
            "success": True,
            "updated_world": self.world_settings,
            "agent": self.agent_id
        }
    
    async def _get_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取特定场景的世界背景"""
        chapter = task.get("chapter", 1)
        scene_location = task.get("scene_location", "")
        
        # 根据场景位置提取相关背景
        relevant_context = {
            "basic_info": self.world_settings.get("basic_info", {}),
            "current_location": {},
            "relevant_history": [],
            "cultural_notes": {}
        }
        
        # 提取地理位置信息
        geography = self.world_settings.get("geography", {})
        locations = geography.get("locations", [])
        
        for loc in locations:
            if scene_location in loc.get("name", ""):
                relevant_context["current_location"] = loc
                break
        
        return {
            "success": True,
            "context": relevant_context,
            "chapter": chapter,
            "agent": self.agent_id
        }
    
    def validate_consistency(self, new_element: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证新元素与世界观的一致性
        
        Args:
            new_element: 新添加的世界元素
            
        Returns:
            验证结果
        """
        # 简化实现，实际应该使用LLM进行验证
        return {
            "consistent": True,
            "conflicts": [],
            "suggestions": []
        }
