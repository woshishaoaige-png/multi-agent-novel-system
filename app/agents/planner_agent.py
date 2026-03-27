"""
首席规划师 Agent

负责：
- 理解用户需求
- 生成故事大纲
- 制定整体架构
- 协调其他Agent
"""

from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent, AgentRole


class PlannerAgent(BaseAgent):
    """
    首席规划师 Agent
    
    参考MuMuAINovel的大纲生成功能，扩展为多Agent协作的规划能力
    """
    
    def __init__(self, agent_id: str, llm_client: Any, style: Optional[Any] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.PLANNER,
            name="首席规划师",
            description="负责故事整体规划、大纲生成和Agent协调",
            llm_client=llm_client,
            style=style
        )
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的小说首席规划师，拥有丰富的故事架构经验。

你的职责：
1. 深入理解用户的创作意图和需求
2. 设计完整的故事大纲和章节结构
3. 协调各专业Agent的工作分配
4. 确保故事的连贯性和吸引力

工作原则：
- 注重故事的戏剧性和张力
- 合理安排情节节奏
- 预留角色成长空间
- 考虑伏笔和呼应
- 平衡各章节篇幅

输出要求：
- 结构清晰，层次分明
- 内容具体，可操作性强
- 使用JSON格式输出结构化数据
"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行规划任务
        
        Args:
            task: {
                "type": "create_outline" | "refine_outline" | "assign_tasks",
                "user_input": str,  # 用户需求
                "genre": str,  # 小说类型
                "target_chapters": int,  # 目标章节数
                "existing_outline": Optional[str],  # 已有大纲（用于优化）
            }
        """
        task_type = task.get("type", "create_outline")
        
        if task_type == "create_outline":
            return await self._create_outline(task)
        elif task_type == "refine_outline":
            return await self._refine_outline(task)
        elif task_type == "assign_tasks":
            return await self._assign_tasks(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
    
    async def _create_outline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """创建故事大纲"""
        user_input = task.get("user_input", "")
        genre = task.get("genre", "general")
        target_chapters = task.get("target_chapters", 20)
        
        prompt = f"""请为以下小说创作需求设计完整的故事大纲：

【创作需求】
{user_input}

【小说类型】{genre}
【目标章节数】{target_chapters}章

请输出完整的规划方案，包含以下内容：

1. **故事概要** (200-300字)
2. **核心主题**
3. **主要情节线**
   - 主线
   - 支线1
   - 支线2
4. **章节规划** (每章包含：标题、概要、关键事件、预计字数)
5. **节奏设计** (起承转合的安排)
6. **伏笔规划** (重要伏笔的设置和回收)
7. **Agent工作分配建议**

输出格式：JSON
{{
    "story_summary": "故事概要",
    "core_theme": "核心主题",
    "plot_lines": {{
        "main": "主线描述",
        "sub1": "支线1描述",
        "sub2": "支线2描述"
    }},
    "chapters": [
        {{
            "chapter_num": 1,
            "title": "章节标题",
            "summary": "章节概要",
            "key_events": ["事件1", "事件2"],
            "word_count": 3000,
            "agents_needed": ["world_builder", "character_designer", "writer"]
        }}
    ],
    "pacing_design": {{
        "setup": "1-5章",
        "rising_action": "6-12章",
        "climax": "13-17章",
        "resolution": "18-20章"
    }},
    "foreshadowing": [
        {{
            "hint": "伏笔内容",
            "chapter_set": 3,
            "chapter_resolve": 15
        }}
    ],
    "agent_assignments": {{
        "world_builder": ["世界观设定任务"],
        "character_designer": ["主要角色设计"],
        "plot_planner": ["情节细节规划"]
    }}
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            outline = json.loads(response)
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原始文本
            outline = {"raw_outline": response}
        
        # 保存到记忆
        self.update_memory("current_outline", outline)
        
        return {
            "success": True,
            "outline": outline,
            "agent": self.agent_id,
            "next_steps": [
                "调用WorldBuilder创建世界观",
                "调用CharacterDesigner设计角色",
                "调用PlotPlanner细化情节"
            ]
        }
    
    async def _refine_outline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """优化现有大纲"""
        existing_outline = task.get("existing_outline", "")
        feedback = task.get("feedback", "")
        
        prompt = f"""请根据反馈优化以下故事大纲：

【现有大纲】
{json.dumps(existing_outline, ensure_ascii=False, indent=2)}

【优化反馈】
{feedback}

请输出优化后的大纲，保持原有JSON格式。
"""
        
        response = await self._call_llm(prompt)
        
        try:
            refined = json.loads(response)
        except json.JSONDecodeError:
            refined = {"raw_refined": response}
        
        return {
            "success": True,
            "refined_outline": refined,
            "agent": self.agent_id
        }
    
    async def _assign_tasks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分配任务给其他Agent"""
        outline = task.get("outline", self.get_memory("current_outline"))
        available_agents = task.get("available_agents", [])
        
        prompt = f"""请为以下大纲分配Agent任务：

【大纲】
{json.dumps(outline, ensure_ascii=False, indent=2)}

【可用Agent】
{json.dumps(available_agents, ensure_ascii=False, indent=2)}

请输出任务分配方案：
{{
    "assignments": [
        {{
            "agent_id": "agent_id",
            "task": "具体任务描述",
            "priority": 1-5,
            "dependencies": ["依赖的其他任务"],
            "expected_output": "预期输出"
        }}
    ],
    "workflow": "顺序/并行/混合",
    "timeline": "预计完成时间"
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            assignments = json.loads(response)
        except json.JSONDecodeError:
            assignments = {"raw_assignments": response}
        
        return {
            "success": True,
            "assignments": assignments,
            "agent": self.agent_id
        }
    
    async def coordinate_writing(
        self,
        chapter_num: int,
        collaborators: Dict[str, BaseAgent]
    ) -> Dict[str, Any]:
        """
        协调章节写作
        
        这是Planner的核心协调功能，负责：
        1. 调用WorldBuilder确认世界观
        2. 调用CharacterDesigner确认角色状态
        3. 调用PlotPlanner确认情节走向
        4. 调用Writer执行写作
        5. 调用Editor进行润色
        """
        outline = self.get_memory("current_outline")
        chapter_info = outline.get("chapters", [])[chapter_num - 1] if outline else {}
        
        results = {}
        
        # 1. 获取世界观信息
        if "world_builder" in collaborators:
            world_info = await self.collaborate(
                collaborators["world_builder"],
                {
                    "action": "get_world_context",
                    "chapter": chapter_num,
                    "scene_location": chapter_info.get("scene", "")
                }
            )
            results["world_context"] = world_info
        
        # 2. 获取角色信息
        if "character_designer" in collaborators:
            character_info = await self.collaborate(
                collaborators["character_designer"],
                {
                    "action": "get_character_context",
                    "chapter": chapter_num,
                    "involved_characters": chapter_info.get("characters", [])
                }
            )
            results["character_context"] = character_info
        
        # 3. 获取情节指导
        if "plot_planner" in collaborators:
            plot_guidance = await self.collaborate(
                collaborators["plot_planner"],
                {
                    "action": "get_plot_guidance",
                    "chapter": chapter_num,
                    "key_events": chapter_info.get("key_events", [])
                }
            )
            results["plot_guidance"] = plot_guidance
        
        return {
            "success": True,
            "coordination_results": results,
            "ready_for_writing": True,
            "writer_input": {
                "chapter_info": chapter_info,
                **results
            }
        }
