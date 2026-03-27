"""
角色设计师 Agent

负责：
- 设计主要角色
- 维护角色档案
- 追踪角色状态变化
"""

from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent, AgentRole


class CharacterAgent(BaseAgent):
    """
    角色设计师 Agent
    
    参考MuMuAINovel的角色管理功能
    """
    
    def __init__(self, agent_id: str, llm_client: Any, style: Optional[Any] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.CHARACTER_DESIGNER,
            name="角色设计师",
            description="负责设计和维护小说角色",
            llm_client=llm_client,
            style=style
        )
        
        # 角色档案库
        self.characters: Dict[str, Dict[str, Any]] = {}
    
    def get_system_prompt(self) -> str:
        return """你是一位专业的角色设计师，擅长创造鲜活立体的人物。

设计原则：
1. 性格鲜明，有独特标签
2. 背景完整，动机清晰
3. 成长弧线明确
4. 关系网络复杂
5. 避免脸谱化

角色档案包含：
- 基本信息
- 外貌特征
- 性格特点
- 背景故事
- 目标动机
- 成长弧线
- 人际关系
- 经典台词
"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行角色设计任务
        
        Args:
            task: {
                "type": "create_character" | "update_character" | "get_context" | "design_relationships",
                "character_info": Dict,
                "character_id": str
            }
        """
        task_type = task.get("type", "create_character")
        
        if task_type == "create_character":
            return await self._create_character(task)
        elif task_type == "update_character":
            return await self._update_character(task)
        elif task_type == "get_context":
            return await self._get_context(task)
        elif task_type == "design_relationships":
            return await self._design_relationships(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
    
    async def _create_character(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """创建新角色"""
        character_info = task.get("character_info", {})
        
        prompt = f"""请设计一个完整的角色档案。

【角色基础信息】
{json.dumps(character_info, ensure_ascii=False, indent=2)}

请输出完整的角色档案，包含以下模块：

1. **基本信息**
   - 姓名
   - 性别
   - 年龄
   - 身份/职业
   - 称号/别名

2. **外貌特征**
   - 整体形象
   - 面部特征
   - 身材体型
   - 穿着风格
   - 标志性特征

3. **性格特点**
   - 核心性格（3-5个关键词）
   - 性格层次（表面vs内在）
   - 性格缺陷
   - 性格闪光点

4. **背景故事**
   - 出身背景
   - 成长经历
   - 重要事件
   - 创伤/阴影
   - 美好回忆

5. **目标与动机**
   - 表面目标
   - 深层动机
   - 内心渴望
   - 恐惧/顾虑

6. **成长弧线**
   - 起点状态
   - 成长方向
   - 关键转折点
   - 预期终点

7. **能力与技能**
   - 主要能力
   - 技能等级
   - 特殊技能
   - 弱点/限制

8. **人际关系**
   - 重要关系人
   - 关系类型
   - 关系动态

9. **经典台词**
   - 代表性台词（3-5句）
   - 口头禅

10. **创作备注**
    - 设计灵感
    - 参考原型
    - 注意事项

输出格式：JSON
"""
        
        response = await self._call_llm(prompt)
        
        try:
            character = json.loads(response)
        except json.JSONDecodeError:
            character = {"raw_character": response}
        
        # 分配角色ID
        character_id = character.get("basic_info", {}).get("name", f"character_{len(self.characters)}")
        self.characters[character_id] = character
        
        return {
            "success": True,
            "character_id": character_id,
            "character": character,
            "agent": self.agent_id
        }
    
    async def _update_character(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """更新角色状态"""
        character_id = task.get("character_id", "")
        updates = task.get("updates", {})
        
        if character_id not in self.characters:
            return {
                "success": False,
                "error": f"角色 {character_id} 不存在"
            }
        
        # 更新角色信息
        character = self.characters[character_id]
        for key, value in updates.items():
            if key in character and isinstance(character[key], dict) and isinstance(value, dict):
                character[key].update(value)
            else:
                character[key] = value
        
        return {
            "success": True,
            "character_id": character_id,
            "updated_character": character,
            "agent": self.agent_id
        }
    
    async def _get_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取角色上下文"""
        chapter = task.get("chapter", 1)
        involved_characters = task.get("involved_characters", [])
        
        context = {
            "characters": {},
            "relationships": {},
            "current_states": {}
        }
        
        for char_id in involved_characters:
            if char_id in self.characters:
                char = self.characters[char_id]
                context["characters"][char_id] = {
                    "name": char.get("basic_info", {}).get("name", ""),
                    "current_status": char.get("current_status", "活跃"),
                    "key_traits": char.get("personality", {}).get("core_traits", []),
                    "current_goal": char.get("motivation", {}).get("surface_goal", "")
                }
        
        return {
            "success": True,
            "context": context,
            "chapter": chapter,
            "agent": self.agent_id
        }
    
    async def _design_relationships(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """设计角色关系网"""
        characters = task.get("characters", [])
        
        prompt = f"""请为以下角色设计关系网络。

【角色列表】
{json.dumps(characters, ensure_ascii=False, indent=2)}

请设计：
1. 两两之间的关系类型（朋友、敌人、恋人、师徒等）
2. 关系的历史渊源
3. 当前关系状态
4. 关系动态（如何发展变化）
5. 关系中的冲突和张力

输出格式：JSON
{{
    "relationships": [
        {{
            "character1": "角色1",
            "character2": "角色2",
            "relationship_type": "关系类型",
            "history": "关系历史",
            "current_status": "当前状态",
            "dynamics": "关系动态",
            "conflict": "冲突点"
        }}
    ],
    "relationship_map": "关系图描述"
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            relationships = json.loads(response)
        except json.JSONDecodeError:
            relationships = {"raw_relationships": response}
        
        return {
            "success": True,
            "relationships": relationships,
            "agent": self.agent_id
        }
    
    def get_character_list(self) -> List[Dict[str, Any]]:
        """获取角色列表"""
        return [
            {
                "id": char_id,
                "name": char.get("basic_info", {}).get("name", ""),
                "role": char.get("basic_info", {}).get("role", "")
            }
            for char_id, char in self.characters.items()
        ]
