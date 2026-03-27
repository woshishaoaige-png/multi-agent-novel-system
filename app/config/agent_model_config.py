"""
Agent模型配置系统

支持为每个Agent单独配置不同的大模型，实现灵活的模型分配策略。
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# YAML支持（可选）
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ModelCapability(Enum):
    """模型能力"""
    GENERAL = "general"           # 通用能力
    CREATIVE = "creative"        # 创意写作
    ANALYSIS = "analysis"         # 分析能力
    LONG_CONTEXT = "long_context" # 长上下文
    FAST = "fast"                # 快速响应
    CHEAP = "cheap"              # 成本优化


@dataclass
class ModelInfo:
    """模型信息"""
    provider: str                    # 提供商 (openai, anthropic, gemini, deepseek等)
    model_name: str                  # 模型名称
    api_key: Optional[str] = None    # API密钥（可以从环境变量引用）
    base_url: Optional[str] = None   # 自定义API地址
    capabilities: List[ModelCapability] = field(default_factory=list)  # 模型能力标签
    max_tokens: int = 4000           # 最大输出tokens
    temperature: float = 0.7         # 温度参数
    cost_tier: str = "medium"        # 成本等级: cheap, medium, expensive
    description: str = ""            # 模型描述
    context_window: int = 128000      # 上下文窗口大小
    
    def __hash__(self):
        return hash((self.provider, self.model_name))


@dataclass
class AgentModelConfig:
    """Agent模型配置"""
    agent_role: str                  # Agent角色
    primary_model: str               # 主要使用的模型ID
    fallback_models: List[str] = field(default_factory=list)  # 备用模型列表
    max_retries: int = 3            # 最大重试次数
    timeout: float = 120.0           # 超时时间(秒)
    custom_params: Dict[str, Any] = field(default_factory=dict)  # 自定义参数
    
    # 任务类型到模型的映射（可选）
    task_model_map: Dict[str, str] = field(default_factory=dict)


class AgentModelRegistry:
    """
    Agent模型注册表
    
    管理所有可用模型和Agent的模型配置
    """
    
    def __init__(self):
        # 可用模型字典 {model_id: ModelInfo}
        self.available_models: Dict[str, ModelInfo] = {}
        
        # Agent模型配置字典 {agent_role: AgentModelConfig}
        self.agent_configs: Dict[str, AgentModelConfig] = {}
        
        # 默认配置
        self._init_default_configs()
    
    def _init_default_configs(self):
        """初始化默认配置"""
        # 默认Agent模型配置
        default_configs = {
            "planner": {
                "agent_role": "planner",
                "primary_model": "gpt-4",
                "capabilities_needed": [ModelCapability.ANALYSIS, ModelCapability.GENERAL],
                "description": "首席规划师需要强大的分析和规划能力"
            },
            "world_builder": {
                "agent_role": "world_builder", 
                "primary_model": "gpt-4",
                "capabilities_needed": [ModelCapability.CREATIVE, ModelCapability.LONG_CONTEXT],
                "description": "世界构建师需要创意和长上下文能力"
            },
            "character_designer": {
                "agent_role": "character_designer",
                "primary_model": "gpt-4",
                "capabilities_needed": [ModelCapability.CREATIVE, ModelCapability.ANALYSIS],
                "description": "角色设计师需要创意和分析能力"
            },
            "writer": {
                "agent_role": "writer",
                "primary_model": "gpt-4",
                "capabilities_needed": [ModelCapability.CREATIVE],
                "description": "主笔作家需要强大的创意写作能力"
            },
            "editor": {
                "agent_role": "editor",
                "primary_model": "gpt-4",
                "capabilities_needed": [ModelCapability.GENERAL],
                "description": "风格编辑需要良好的语言处理能力"
            }
        }
        
        # 将默认配置存入agent_configs
        for role, config in default_configs.items():
            self.agent_configs[role] = AgentModelConfig(
                agent_role=config["agent_role"],
                primary_model=config["primary_model"],
                fallback_models=["claude-3-opus", "gpt-3.5-turbo"]
            )
    
    def register_model(self, model_id: str, model_info: ModelInfo):
        """注册一个可用模型"""
        self.available_models[model_id] = model_info
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self.available_models.get(model_id)
    
    def set_agent_config(self, agent_role: str, config: AgentModelConfig):
        """设置Agent的模型配置"""
        self.agent_configs[agent_role] = config
    
    def get_agent_config(self, agent_role: str) -> Optional[AgentModelConfig]:
        """获取Agent的模型配置"""
        return self.agent_configs.get(agent_role)
    
    def get_model_for_agent(
        self,
        agent_role: str,
        task_type: Optional[str] = None
    ) -> Optional[ModelInfo]:
        """
        根据Agent角色获取合适的模型
        
        Args:
            agent_role: Agent角色
            task_type: 任务类型（可选，用于特定任务选择模型）
            
        Returns:
            模型信息
        """
        config = self.agent_configs.get(agent_role)
        if not config:
            # 返回默认模型
            return self.available_models.get("gpt-4")
        
        # 如果有任务类型映射，使用特定模型
        if task_type and task_type in config.task_model_map:
            model_id = config.task_model_map[task_type]
            return self.available_models.get(model_id)
        
        # 返回主模型
        return self.available_models.get(config.primary_model)
    
    def find_best_model(
        self,
        capabilities: List[ModelCapability],
        cost_constraint: Optional[str] = None
    ) -> Optional[ModelInfo]:
        """
        根据能力和成本约束找到最佳模型
        
        Args:
            capabilities: 需要的模型能力
            cost_constraint: 成本约束 (cheap, medium, expensive)
            
        Returns:
            最合适的模型
        """
        candidates = []
        
        for model_id, model in self.available_models.items():
            # 检查能力是否满足
            if all(cap in model.capabilities for cap in capabilities):
                # 检查成本约束
                if cost_constraint is None or model.cost_tier == cost_constraint:
                    candidates.append((model_id, model))
        
        if not candidates:
            return None
        
        # 优先选择中等成本
        for model_id, model in candidates:
            if model.cost_tier == "medium":
                return model
        
        return candidates[0][1] if candidates else None
    
    def load_from_yaml(self, yaml_path: str):
        """从YAML文件加载配置"""
        path = Path(yaml_path)
        if not path.exists():
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 加载模型配置
        if "models" in config:
            for model_id, model_data in config["models"].items():
                self.register_model(model_id, ModelInfo(
                    provider=model_data.get("provider", "openai"),
                    model_name=model_data.get("model_name", model_id),
                    api_key=model_data.get("api_key"),
                    base_url=model_data.get("base_url"),
                    capabilities=[
                        ModelCapability(c) for c in model_data.get("capabilities", [])
                    ],
                    max_tokens=model_data.get("max_tokens", 4000),
                    temperature=model_data.get("temperature", 0.7),
                    cost_tier=model_data.get("cost_tier", "medium"),
                    description=model_data.get("description", ""),
                    context_window=model_data.get("context_window", 128000)
                ))
        
        # 加载Agent配置
        if "agent_models" in config:
            for agent_role, agent_data in config["agent_models"].items():
                self.agent_configs[agent_role] = AgentModelConfig(
                    agent_role=agent_role,
                    primary_model=agent_data.get("primary_model", "gpt-4"),
                    fallback_models=agent_data.get("fallback_models", []),
                    max_retries=agent_data.get("max_retries", 3),
                    timeout=agent_data.get("timeout", 120.0),
                    custom_params=agent_data.get("custom_params", {}),
                    task_model_map=agent_data.get("task_model_map", {})
                )
    
    def save_to_yaml(self, yaml_path: str):
        """保存配置到YAML文件"""
        config = {
            "models": {},
            "agent_models": {}
        }
        
        # 序列化模型
        for model_id, model in self.available_models.items():
            config["models"][model_id] = {
                "provider": model.provider,
                "model_name": model.model_name,
                "api_key": model.api_key,
                "base_url": model.base_url,
                "capabilities": [c.value for c in model.capabilities],
                "max_tokens": model.max_tokens,
                "temperature": model.temperature,
                "cost_tier": model.cost_tier,
                "description": model.description,
                "context_window": model.context_window
            }
        
        # 序列化Agent配置
        for agent_role, agent_config in self.agent_configs.items():
            config["agent_models"][agent_role] = {
                "primary_model": agent_config.primary_model,
                "fallback_models": agent_config.fallback_models,
                "max_retries": agent_config.max_retries,
                "timeout": agent_config.timeout,
                "custom_params": agent_config.custom_params,
                "task_model_map": agent_config.task_model_map
            }
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型"""
        return [
            {
                "model_id": model_id,
                "provider": model.provider,
                "model_name": model.model_name,
                "capabilities": [c.value for c in model.capabilities],
                "cost_tier": model.cost_tier,
                "description": model.description
            }
            for model_id, model in self.available_models.items()
        ]
    
    def list_agent_configs(self) -> List[Dict[str, Any]]:
        """列出所有Agent配置"""
        return [
            {
                "agent_role": role,
                "primary_model": config.primary_model,
                "fallback_models": config.fallback_models,
                "max_retries": config.max_retries,
                "timeout": config.timeout
            }
            for role, config in self.agent_configs.items()
        ]


# 全局注册表实例
_global_registry: Optional[AgentModelRegistry] = None


def get_model_registry() -> AgentModelRegistry:
    """获取全局模型注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentModelRegistry()
    return _global_registry


def init_model_registry(config_path: Optional[str] = None) -> AgentModelRegistry:
    """初始化模型注册表"""
    global _global_registry
    _global_registry = AgentModelRegistry()
    
    if config_path and Path(config_path).exists():
        _global_registry.load_from_yaml(config_path)
    
    return _global_registry
