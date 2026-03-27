"""
主笔作家 Agent

负责：
- 根据大纲撰写章节内容
- 应用指定写作风格
- 保持叙事连贯性
"""

from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent, AgentRole, WriterStyle


class WriterAgent(BaseAgent):
    """
    主笔作家 Agent
    
    核心功能：
    1. 根据大纲和上下文撰写章节
    2. 应用学习到的作家风格
    3. 保持与前文的连贯性
    4. 支持多种写作风格切换
    """
    
    def __init__(
        self,
        agent_id: str,
        llm_client: Any,
        style: Optional[WriterStyle] = None
    ):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.WRITER,
            name="主笔作家",
            description="负责撰写小说章节内容",
            llm_client=llm_client,
            style=style
        )
        
        # 写作统计
        self.writing_stats = {
            "total_chapters": 0,
            "total_words": 0,
            "avg_quality_score": 0.0
        }
    
    def get_system_prompt(self) -> str:
        base_prompt = """你是一位专业的小说作家，擅长创作引人入胜的故事。

写作原则：
1. **场景描写**：生动具体，调动读者感官
2. **人物刻画**：性格鲜明，行为符合人设
3. **对话设计**：自然流畅，推动情节发展
4. **节奏把控**：张弛有度，保持阅读兴趣
5. **情感表达**：真挚动人，引发共鸣

技术要求：
- 每章字数控制在3000-5000字
- 段落分明，层次清晰
- 避免重复和冗余
- 注意前后呼应
"""
        
        if self.style:
            base_prompt += f"\n\n{self.style.to_prompt()}"
        
        return base_prompt
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行写作任务
        
        Args:
            task: {
                "type": "write_chapter" | "rewrite_chapter" | "polish",
                "chapter_num": int,
                "chapter_title": str,
                "outline": str,
                "world_context": Dict,
                "character_context": Dict,
                "plot_guidance": Dict,
                "previous_chapters": List[str],
                "target_word_count": int,
                "feedback": Optional[str]  # 用于重写
            }
        """
        task_type = task.get("type", "write_chapter")
        
        if task_type == "write_chapter":
            return await self._write_chapter(task)
        elif task_type == "rewrite_chapter":
            return await self._rewrite_chapter(task)
        elif task_type == "polish":
            return await self._polish(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
    
    async def _write_chapter(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """撰写新章节"""
        chapter_num = task.get("chapter_num", 1)
        chapter_title = task.get("chapter_title", f"第{chapter_num}章")
        outline = task.get("outline", {})
        world_context = task.get("world_context", {})
        character_context = task.get("character_context", {})
        plot_guidance = task.get("plot_guidance", {})
        previous_chapters = task.get("previous_chapters", [])
        target_word_count = task.get("target_word_count", 3500)
        
        # 构建写作提示词
        prompt = self._build_writing_prompt(
            chapter_num=chapter_num,
            chapter_title=chapter_title,
            outline=outline,
            world_context=world_context,
            character_context=character_context,
            plot_guidance=plot_guidance,
            previous_chapters=previous_chapters,
            target_word_count=target_word_count
        )
        
        self.status = self.__class__.status_class.WORKING if hasattr(self, 'status_class') else None
        
        # 调用LLM生成内容
        content = await self._call_llm(prompt)
        
        # 更新统计
        self.writing_stats["total_chapters"] += 1
        self.writing_stats["total_words"] += len(content)
        
        # 保存到记忆
        self.update_memory(f"chapter_{chapter_num}", content)
        self.memory.add_to_short_term({
            "chapter": chapter_num,
            "title": chapter_title,
            "preview": content[:200]
        })
        
        return {
            "success": True,
            "chapter_num": chapter_num,
            "title": chapter_title,
            "content": content,
            "word_count": len(content),
            "agent": self.agent_id,
            "style_applied": self.style.name if self.style else "default"
        }
    
    def _build_writing_prompt(
        self,
        chapter_num: int,
        chapter_title: str,
        outline: Dict[str, Any],
        world_context: Dict[str, Any],
        character_context: Dict[str, Any],
        plot_guidance: Dict[str, Any],
        previous_chapters: List[str],
        target_word_count: int
    ) -> str:
        """构建写作提示词"""
        
        # 前文摘要（最近3章）
        previous_summary = ""
        if previous_chapters:
            recent = previous_chapters[-3:]
            previous_summary = "\n\n".join([
                f"【第{i+1}章摘要】{ch[:300]}..."
                for i, ch in enumerate(recent)
            ])
        
        return f"""请撰写小说章节。

【章节信息】
- 章节号：第{chapter_num}章
- 章节标题：{chapter_title}

【章节大纲】
{json.dumps(outline, ensure_ascii=False, indent=2)}

【世界观背景】
{json.dumps(world_context, ensure_ascii=False, indent=2)}

【角色信息】
{json.dumps(character_context, ensure_ascii=False, indent=2)}

【情节指导】
{json.dumps(plot_guidance, ensure_ascii=False, indent=2)}

【前文摘要】
{previous_summary}

【写作要求】
- 目标字数：{target_word_count}字
- 必须包含：场景描写、对话、心理活动
- 注意：与前文保持连贯，人物行为符合设定

请直接输出章节正文，不需要额外的说明文字。
"""
    
    async def _rewrite_chapter(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """根据反馈重写章节"""
        original_content = task.get("original_content", "")
        feedback = task.get("feedback", "")
        chapter_num = task.get("chapter_num", 1)
        
        prompt = f"""请根据反馈重写以下章节。

【原章节内容】
{original_content}

【修改反馈】
{feedback}

请重写该章节，保留核心情节，根据反馈进行改进。
直接输出重写后的正文。
"""
        
        content = await self._call_llm(prompt)
        
        return {
            "success": True,
            "chapter_num": chapter_num,
            "content": content,
            "word_count": len(content),
            "agent": self.agent_id,
            "rewrite": True
        }
    
    async def _polish(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """润色内容"""
        content = task.get("content", "")
        polish_type = task.get("polish_type", "general")  # general, style, grammar
        
        polish_prompts = {
            "general": "请对以下内容进行整体润色，提升文学性和可读性：",
            "style": "请对以下内容进行风格化润色，增强语言特色：",
            "grammar": "请修正以下内容中的语法和表达问题："
        }
        
        prompt = f"""{polish_prompts.get(polish_type, polish_prompts["general"])}

【原文】
{content}

请输出润色后的内容，保持原意不变。
"""
        
        polished = await self._call_llm(prompt)
        
        return {
            "success": True,
            "original": content,
            "polished": polished,
            "polish_type": polish_type,
            "agent": self.agent_id
        }
    
    @classmethod
    async def create_from_text(
        cls,
        name: str,
        sample_texts: List[str],
        llm_client: Any,
        style_description: str = ""
    ) -> WriterStyle:
        """
        从样本文本创建作家风格
        
        这是本系统的核心功能之一，允许用户上传喜欢的作家文章
        来训练/塑造不同的作家Agent
        """
        # 分析文本风格
        analysis_prompt = f"""请分析以下文本的写作风格，提取特征：

【样本文本】
{chr(10).join([f"---样本{i+1}---\n{text[:2000]}" for i, text in enumerate(sample_texts)])}

请分析并输出以下维度的特征：
1. 词汇特征（常用词汇类型、修辞手法等）
2. 句式特点（长短句搭配、句式结构等）
3. 叙事特征（叙事视角、节奏把控等）
4. 对话风格（对话特点、语气等）
5. 节奏风格（整体叙事节奏）

输出格式：JSON
{{
    "vocabulary_features": ["特征1", "特征2"],
    "sentence_patterns": ["特点1", "特点2"],
    "narrative_features": ["特征1", "特征2"],
    "dialogue_style": "对话风格描述",
    "pacing_style": "节奏风格描述",
    "system_prompt": "用于指导AI模仿该风格的系统提示词"
}}
"""
        
        response = await llm_client.complete(
            prompt=analysis_prompt,
            system_prompt="你是一位文学分析专家，擅长分析作家的写作风格。"
        )
        
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError:
            # 如果解析失败，使用默认结构
            analysis = {
                "vocabulary_features": ["优美", "生动"],
                "sentence_patterns": ["长短结合", "节奏流畅"],
                "narrative_features": ["第三人称叙事", "细腻描写"],
                "dialogue_style": "自然流畅的对话",
                "pacing_style": "张弛有度",
                "system_prompt": response
            }
        
        style = WriterStyle(
            name=name,
            description=style_description,
            vocabulary_features=analysis.get("vocabulary_features", []),
            sentence_patterns=analysis.get("sentence_patterns", []),
            narrative_features=analysis.get("narrative_features", []),
            dialogue_style=analysis.get("dialogue_style", ""),
            pacing_style=analysis.get("pacing_style", ""),
            system_prompt=analysis.get("system_prompt", ""),
            sample_texts=sample_texts
        )
        
        return style
    
    def get_stats(self) -> Dict[str, Any]:
        """获取写作统计"""
        return {
            **self.writing_stats,
            "avg_words_per_chapter": (
                self.writing_stats["total_words"] / self.writing_stats["total_chapters"]
                if self.writing_stats["total_chapters"] > 0 else 0
            )
        }
