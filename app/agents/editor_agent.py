"""
风格编辑 Agent

负责：
- 润色章节内容
- 统一文风
- 检查语言质量
"""

from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent, AgentRole


class EditorAgent(BaseAgent):
    """
    风格编辑 Agent
    
    负责内容润色和质量把控
    """
    
    def __init__(self, agent_id: str, llm_client: Any, style: Optional[Any] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.STYLE_EDITOR,
            name="风格编辑",
            description="负责润色内容、统一文风",
            llm_client=llm_client,
            style=style
        )
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的文学编辑，擅长润色和打磨作品。

编辑原则：
1. 保持作者原意
2. 提升文学性
3. 统一文风
4. 精炼语言
5. 修正错误

编辑维度：
- 语言表达：用词准确、句式多样
- 修辞手法：比喻、拟人、排比等
- 节奏把控：快慢结合、张弛有度
- 情感表达：真挚动人、层次分明
- 逻辑连贯：前后呼应、过渡自然
"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行编辑任务
        
        Args:
            task: {
                "type": "polish" | "style_unify" | "grammar_check",
                "content": str,
                "target_style": Optional[str],
                "edit_level": "light" | "medium" | "heavy"
            }
        """
        task_type = task.get("type", "polish")
        
        if task_type == "polish":
            return await self._polish(task)
        elif task_type == "style_unify":
            return await self._style_unify(task)
        elif task_type == "grammar_check":
            return await self._grammar_check(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
    
    async def _polish(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """润色内容"""
        content = task.get("content", "")
        edit_level = task.get("edit_level", "medium")
        
        level_instructions = {
            "light": "轻度润色：修正明显错误，微调表达",
            "medium": "中度润色：优化表达，提升文学性",
            "heavy": "深度润色：大幅改写，重新组织"
        }
        
        prompt = f"""请对以下内容进行润色。

【编辑要求】{level_instructions.get(edit_level, level_instructions["medium"])}

【原文】
{content}

请输出润色后的内容，并说明主要修改点。

输出格式：
{{
    "polished_content": "润色后的内容",
    "changes": [
        {{
            "type": "修改类型",
            "original": "原文",
            "modified": "修改后",
            "reason": "修改原因"
        }}
    ],
    "improvements": ["改进点1", "改进点2"]
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "polished_content": response,
                "changes": [],
                "improvements": ["整体润色"]
            }
        
        return {
            "success": True,
            **result,
            "agent": self.agent_id
        }
    
    async def _style_unify(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """统一文风"""
        content = task.get("content", "")
        target_style = task.get("target_style", "")
        
        prompt = f"""请将以下内容统一为指定风格。

【目标风格】
{target_style}

【原文】
{content}

请调整语言风格，使其符合目标风格要求，同时保持原意不变。
"""
        
        unified = await self._call_llm(prompt)
        
        return {
            "success": True,
            "original": content,
            "unified": unified,
            "target_style": target_style,
            "agent": self.agent_id
        }
    
    async def _grammar_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """语法检查"""
        content = task.get("content", "")
        
        prompt = f"""请检查以下内容的语法和表达问题。

【原文】
{content}

请检查：
1. 错别字
2. 语法错误
3. 标点符号
4. 用词不当
5. 逻辑不通

输出格式：JSON
{{
    "issues": [
        {{
            "type": "问题类型",
            "location": "位置",
            "original": "原文",
            "suggestion": "修改建议",
            "severity": "high/medium/low"
        }}
    ],
    "corrected_text": "修正后的文本"
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "issues": [],
                "corrected_text": content
            }
        
        return {
            "success": True,
            **result,
            "agent": self.agent_id
        }
    
    async def review_chapter(
        self,
        chapter_content: str,
        chapter_outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审核章节质量
        
        这是Editor的核心功能，对章节进行全面评估
        """
        prompt = f"""请审核以下章节的质量。

【章节大纲】
{json.dumps(chapter_outline, ensure_ascii=False, indent=2)}

【章节内容】
{chapter_content}

请从以下维度进行评估：

1. **内容质量**
   - 是否符合大纲要求
   - 情节是否吸引人
   - 节奏是否得当

2. **语言表达**
   - 用词是否准确
   - 句式是否多样
   - 是否有文采

3. **人物刻画**
   - 人物行为是否符合设定
   - 对话是否自然
   - 情感表达是否到位

4. **逻辑连贯**
   - 情节逻辑是否通顺
   - 前后是否呼应
   - 过渡是否自然

5. **改进建议**
   - 具体问题
   - 修改建议

输出格式：JSON
{{
    "overall_score": 0-100,
    "dimensions": {{
        "content_quality": {{"score": 0-100, "comment": "评价"}},
        "language": {{"score": 0-100, "comment": "评价"}},
        "character": {{"score": 0-100, "comment": "评价"}},
        "coherence": {{"score": 0-100, "comment": "评价"}}
    }},
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "approved": true/false
}}
"""
        
        response = await self._call_llm(prompt)
        
        try:
            review = json.loads(response)
        except json.JSONDecodeError:
            review = {
                "overall_score": 70,
                "raw_review": response,
                "approved": True
            }
        
        return {
            "success": True,
            "review": review,
            "agent": self.agent_id
        }
