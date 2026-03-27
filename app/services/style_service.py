"""
作家风格学习服务

核心功能：
- 从文本中提取作家风格
- 存储和管理风格模板
- 风格混合和迁移
"""

from typing import Dict, List, Any, Optional
import json
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

from ..agents.base_agent import WriterStyle


class StyleService:
    """
    作家风格学习服务
    
    这是本系统的核心创新功能，允许用户：
    1. 上传喜欢的作家文章
    2. 系统自动分析并提取风格特征
    3. 创建可复用的作家Agent
    4. 支持风格混合
    """
    
    def __init__(self, storage_path: str = "./data/styles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已保存的风格
        self.styles: Dict[str, WriterStyle] = {}
        self._load_styles()
    
    def _load_styles(self):
        """加载已保存的风格"""
        for style_file in self.storage_path.glob("*.json"):
            try:
                with open(style_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    style = WriterStyle(**data)
                    self.styles[style.name] = style
            except Exception as e:
                print(f"加载风格文件失败 {style_file}: {e}")
    
    def _save_style(self, style: WriterStyle):
        """保存风格到文件"""
        style_file = self.storage_path / f"{self._sanitize_filename(style.name)}.json"
        with open(style_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(style), f, ensure_ascii=False, indent=2)
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
    
    async def analyze_style(
        self,
        name: str,
        sample_texts: List[str],
        llm_client: Any,
        description: str = ""
    ) -> WriterStyle:
        """
        分析文本风格
        
        这是核心功能，使用LLM分析作家的写作风格
        
        Args:
            name: 风格名称（如"金庸风格"）
            sample_texts: 样本文本列表
            llm_client: LLM客户端
            description: 风格描述
            
        Returns:
            WriterStyle对象
        """
        # 构建分析提示词
        analysis_prompt = self._build_analysis_prompt(sample_texts)
        
        # 调用LLM分析
        response = await llm_client.complete(
            prompt=analysis_prompt,
            system_prompt="你是一位专业的文学分析专家，擅长分析作家的写作风格特征。"
        )
        
        # 解析分析结果
        style_features = self._parse_style_analysis(response)
        
        # 生成系统提示词
        system_prompt = await self._generate_system_prompt(
            style_features,
            name,
            llm_client
        )
        
        # 创建风格对象
        style = WriterStyle(
            name=name,
            description=description or f"学习自{name}的写作风格",
            vocabulary_features=style_features.get("vocabulary_features", []),
            sentence_patterns=style_features.get("sentence_patterns", []),
            narrative_features=style_features.get("narrative_features", []),
            dialogue_style=style_features.get("dialogue_style", ""),
            pacing_style=style_features.get("pacing_style", ""),
            system_prompt=system_prompt,
            sample_texts=sample_texts[:3]  # 只保存前3个样本
        )
        
        # 保存风格
        self.styles[name] = style
        self._save_style(style)
        
        return style
    
    def _build_analysis_prompt(self, sample_texts: List[str]) -> str:
        """构建风格分析提示词"""
        samples_section = ""
        for i, text in enumerate(sample_texts[:5], 1):  # 最多分析5个样本
            # 截取前3000字符
            truncated = text[:3000]
            samples_section += f"\n{'='*50}\n【样本{i}】\n{'='*50}\n{truncated}\n"
        
        return f"""请深入分析以下文本的写作风格特征。

{samples_section}

请从以下维度进行详细分析：

## 1. 词汇特征
- 常用词汇类型（如：古典词汇、现代词汇、专业术语等）
- 修辞手法偏好（比喻、拟人、排比、对偶等）
- 词汇难度和丰富度
- 是否有特定的用词习惯或口头禅

## 2. 句式特点
- 句子长度偏好（长短句搭配）
- 句式结构（简单句、复合句、倒装句等）
- 标点运用特点
- 段落长度和结构

## 3. 叙事特征
- 叙事视角（第一人称、第三人称全知/限知等）
- 叙事节奏（紧凑、舒缓、快慢交替等）
- 场景描写方式（细腻、简洁、诗意等）
- 心理描写深度

## 4. 对话风格
- 对话特点（自然、书面化、个性化等）
- 对话与叙述的比例
- 对话标签的使用方式

## 5. 整体节奏
- 整体叙事节奏（张弛有度、一气呵成、层层递进等）
- 情节推进方式
- 悬念设置手法

请输出结构化的分析结果，格式如下：

```json
{{
    "vocabulary_features": ["特征1", "特征2", "特征3"],
    "sentence_patterns": ["特点1", "特点2", "特点3"],
    "narrative_features": ["特征1", "特征2", "特征3"],
    "dialogue_style": "对话风格的详细描述",
    "pacing_style": "节奏风格的详细描述"
}}
```
"""
    
    def _parse_style_analysis(self, response: str) -> Dict[str, Any]:
        """解析风格分析结果"""
        try:
            # 尝试从JSON代码块中提取
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            return {
                "vocabulary_features": ["优美的词汇", "丰富的修辞"],
                "sentence_patterns": ["长短句结合", "节奏流畅"],
                "narrative_features": ["细腻的描写", "生动的场景"],
                "dialogue_style": "自然流畅的对话风格",
                "pacing_style": "张弛有度的叙事节奏"
            }
    
    async def _generate_system_prompt(
        self,
        style_features: Dict[str, Any],
        style_name: str,
        llm_client: Any
    ) -> str:
        """生成系统提示词"""
        prompt = f"""请根据以下风格特征，生成一段系统提示词，用于指导AI模仿该写作风格。

【风格名称】{style_name}

【风格特征】
{json.dumps(style_features, ensure_ascii=False, indent=2)}

请生成一段详细的系统提示词，要求：
1. 明确告知AI要模仿的风格
2. 具体说明词汇、句式、叙事等方面的要求
3. 提供具体的写作指导
4. 语言简洁明了，便于AI理解执行

直接输出系统提示词内容，不需要额外的说明。
"""
        
        system_prompt = await llm_client.complete(
            prompt=prompt,
            system_prompt="你是一位专业的提示词工程师。"
        )
        
        return system_prompt
    
    def get_style(self, name: str) -> Optional[WriterStyle]:
        """获取风格"""
        return self.styles.get(name)
    
    def list_styles(self) -> List[Dict[str, str]]:
        """列出所有风格"""
        return [
            {
                "name": style.name,
                "description": style.description
            }
            for style in self.styles.values()
        ]
    
    async def mix_styles(
        self,
        style_names: List[str],
        mix_name: str,
        proportions: Optional[List[float]] = None,
        llm_client: Optional[Any] = None
    ) -> WriterStyle:
        """
        混合多种风格
        
        Args:
            style_names: 要混合的风格名称列表
            mix_name: 混合后的风格名称
            proportions: 各风格的比例（默认平均分配）
            llm_client: LLM客户端
            
        Returns:
            混合后的风格
        """
        if len(style_names) < 2:
            raise ValueError("至少需要两种风格进行混合")
        
        # 获取风格对象
        styles_to_mix = []
        for name in style_names:
            style = self.get_style(name)
            if style is None:
                raise ValueError(f"风格不存在: {name}")
            styles_to_mix.append(style)
        
        # 默认平均分配
        if proportions is None:
            proportions = [1.0 / len(styles_to_mix)] * len(styles_to_mix)
        
        # 混合特征
        mixed_features = self._mix_features(styles_to_mix, proportions)
        
        # 生成混合风格的系统提示词
        if llm_client:
            system_prompt = await self._generate_mixed_system_prompt(
                styles_to_mix,
                proportions,
                mix_name,
                llm_client
            )
        else:
            system_prompt = self._generate_simple_mixed_prompt(styles_to_mix)
        
        mixed_style = WriterStyle(
            name=mix_name,
            description=f"混合风格: {', '.join(style_names)}",
            vocabulary_features=mixed_features["vocabulary_features"],
            sentence_patterns=mixed_features["sentence_patterns"],
            narrative_features=mixed_features["narrative_features"],
            dialogue_style=mixed_features["dialogue_style"],
            pacing_style=mixed_features["pacing_style"],
            system_prompt=system_prompt
        )
        
        # 保存混合风格
        self.styles[mix_name] = mixed_style
        self._save_style(mixed_style)
        
        return mixed_style
    
    def _mix_features(
        self,
        styles: List[WriterStyle],
        proportions: List[float]
    ) -> Dict[str, Any]:
        """混合风格特征"""
        mixed = {
            "vocabulary_features": [],
            "sentence_patterns": [],
            "narrative_features": [],
            "dialogue_style": "",
            "pacing_style": ""
        }
        
        # 合并特征列表
        all_vocab = []
        all_sentences = []
        all_narrative = []
        
        for style, prop in zip(styles, proportions):
            all_vocab.extend(style.vocabulary_features)
            all_sentences.extend(style.sentence_patterns)
            all_narrative.extend(style.narrative_features)
        
        # 去重并保留主要特征
        mixed["vocabulary_features"] = list(dict.fromkeys(all_vocab))[:10]
        mixed["sentence_patterns"] = list(dict.fromkeys(all_sentences))[:10]
        mixed["narrative_features"] = list(dict.fromkeys(all_narrative))[:10]
        
        # 组合对话和节奏风格
        dialogue_parts = [s.dialogue_style for s in styles if s.dialogue_style]
        pacing_parts = [s.pacing_style for s in styles if s.pacing_style]
        
        mixed["dialogue_style"] = "；".join(dialogue_parts) if dialogue_parts else "自然流畅的对话"
        mixed["pacing_style"] = "；".join(pacing_parts) if pacing_parts else "张弛有度的叙事"
        
        return mixed
    
    async def _generate_mixed_system_prompt(
        self,
        styles: List[WriterStyle],
        proportions: List[float],
        mix_name: str,
        llm_client: Any
    ) -> str:
        """生成混合风格的系统提示词"""
        styles_desc = []
        for style, prop in zip(styles, proportions):
            styles_desc.append(f"- {style.name} (占比{prop*100:.0f}%): {style.description}")
        
        prompt = f"""请为混合风格"{mix_name}"生成系统提示词。

【组成风格】
{chr(10).join(styles_desc)}

【各风格特征】
"""
        for style in styles:
            prompt += f"\n【{style.name}】\n"
            prompt += f"词汇: {', '.join(style.vocabulary_features)}\n"
            prompt += f"句式: {', '.join(style.sentence_patterns)}\n"
            prompt += f"叙事: {', '.join(style.narrative_features)}\n"
        
        prompt += """

请生成一段系统提示词，指导AI融合以上风格特点进行写作。
要求：
1. 明确说明要融合的风格
2. 具体指导如何平衡各风格特点
3. 提供实际的写作建议

直接输出系统提示词。
"""
        
        return await llm_client.complete(
            prompt=prompt,
            system_prompt="你是一位专业的提示词工程师。"
        )
    
    def _generate_simple_mixed_prompt(self, styles: List[WriterStyle]) -> str:
        """生成简单的混合风格提示词"""
        style_names = [s.name for s in styles]
        
        return f"""你是一位融合多种写作风格的作家，你的风格融合了：{', '.join(style_names)}。

在写作时，请综合以下风格特点：

【词汇运用】
{chr(10).join([f"- {f}" for s in styles for f in s.vocabulary_features[:3]])}

【句式特点】
{chr(10).join([f"- {p}" for s in styles for p in s.sentence_patterns[:3]])}

【叙事方式】
{chr(10).join([f"- {n}" for s in styles for n in s.narrative_features[:3]])}

请将这些风格特点有机融合，形成独特的写作风格。
"""
    
    def delete_style(self, name: str) -> bool:
        """删除风格"""
        if name in self.styles:
            del self.styles[name]
            style_file = self.storage_path / f"{self._sanitize_filename(name)}.json"
            if style_file.exists():
                style_file.unlink()
            return True
        return False
