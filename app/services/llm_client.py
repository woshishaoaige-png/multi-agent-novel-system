"""
LLM客户端

统一的LLM调用接口，支持多种模型和Agent级别的模型配置
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from enum import Enum

# 导入模型配置
from ..config.agent_model_config import (
    AgentModelRegistry,
    ModelInfo,
    get_model_registry,
    ModelCapability
)


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    DASHSCOPE = "dashscope"      # 阿里云百炼（通义千问）
    MOONSHOT = "moonshot"        # Kimi（月之暗面）
    LOCAL = "local"              # 本地模型
    CUSTOM = "custom"            # 自定义API


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: float = 120.0


class LLMClient:
    """
    统一的LLM客户端
    
    支持：
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Google (Gemini)
    - DeepSeek
    - 本地/自定义模型
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 设置默认base_url
        if config.base_url is None:
            self.config.base_url = self._get_default_base_url(config.provider)
    
    def _get_default_base_url(self, provider: LLMProvider) -> str:
        """获取默认base URL"""
        urls = {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProvider.GEMINI: "https://generativelanguage.googleapis.com/v1",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1",
            LLMProvider.DASHSCOPE: "https://dashscope.aliyuncs.com/compatible-mode/v1",
            LLMProvider.MOONSHOT: "https://api.moonshot.cn/v1",
            LLMProvider.LOCAL: "http://localhost:8000/v1",
            LLMProvider.CUSTOM: "http://localhost:8000/v1",
        }
        return urls.get(provider, urls[LLMProvider.OPENAI])
    
    @staticmethod
    def provider_from_string(provider_str: str) -> LLMProvider:
        """从字符串获取提供商枚举"""
        provider_map = {
            "openai": LLMProvider.OPENAI,
            "anthropic": LLMProvider.ANTHROPIC,
            "claude": LLMProvider.ANTHROPIC,
            "gemini": LLMProvider.GEMINI,
            "deepseek": LLMProvider.DEEPSEEK,
            "dashscope": LLMProvider.DASHSCOPE,
            "qwen": LLMProvider.DASHSCOPE,
            "aliyun": LLMProvider.DASHSCOPE,
            "moonshot": LLMProvider.MOONSHOT,
            "kimi": LLMProvider.MOONSHOT,
            "local": LLMProvider.LOCAL,
            "custom": LLMProvider.CUSTOM,
        }
        return provider_map.get(provider_str.lower(), LLMProvider.OPENAI)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self.session
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        完成文本生成
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            stream: 是否流式输出
            model: 指定模型（可选，默认使用配置中的模型）
            temperature: 指定温度（可选）
            max_tokens: 指定最大tokens（可选）
            
        Returns:
            生成的文本
        """
        # 如果指定了模型，创建新的配置
        if model and model != self.config.model:
            temp_config = LLMConfig(
                provider=self.config.provider,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                model=model,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            temp_client = LLMClient(temp_config)
            result = await temp_client._complete_internal(
                prompt, system_prompt, stream, model,
                temperature or self.config.temperature,
                max_tokens or self.config.max_tokens
            )
            await temp_client.close()
            return result
        
        return await self._complete_internal(
            prompt, system_prompt, stream, 
            model or self.config.model,
            temperature or self.config.temperature,
            max_tokens or self.config.max_tokens
        )
    
    async def _complete_internal(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """内部完成方法"""
        if self.config.provider == LLMProvider.OPENAI:
            return await self._openai_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.GEMINI:
            return await self._gemini_complete(prompt, system_prompt, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.DEEPSEEK:
            return await self._deepseek_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.DASHSCOPE:
            return await self._dashscope_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.MOONSHOT:
            return await self._moonshot_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        elif self.config.provider == LLMProvider.LOCAL or self.config.provider == LLMProvider.CUSTOM:
            return await self._custom_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的提供商: {self.config.provider}")
    
    async def _openai_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI API调用"""
        session = await self._get_session()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI API错误: {error_text}")
            
            if stream:
                return await self._handle_stream_response(response)
            else:
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _anthropic_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Anthropic Claude API调用"""
        session = await self._get_session()
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        async with session.post(
            f"{self.config.base_url}/messages",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic API错误: {error_text}")
            
            result = await response.json()
            return result['content'][0]['text']
    
    async def _gemini_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Google Gemini API调用"""
        session = await self._get_session()
        
        # 合并系统提示词
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        url = f"{self.config.base_url}/models/{model}:generateContent?key={self.config.api_key}"
        
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with session.post(url, json=data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API错误: {error_text}")
            
            result = await response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
    
    async def _deepseek_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """DeepSeek API调用（OpenAI兼容格式）"""
        return await self._openai_complete(prompt, system_prompt, stream, model, temperature, max_tokens)
    
    async def _dashscope_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        阿里云百炼（通义千问）API调用
        
        支持模型：qwen-plus, qwen-plus, qwen-turbo, qwen-long 等
        API文档: https://help.aliyun.com/zh/dashscope/
        """
        session = await self._get_session()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"阿里云百炼API错误: {error_text}")
            
            if stream:
                return await self._handle_stream_response(response)
            else:
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _moonshot_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Kimi（月之暗面）API调用
        
        支持模型：moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
        API文档: https://platform.moonshot.cn/docs/api/chat
        """
        session = await self._get_session()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Kimi API错误: {error_text}")
            
            if stream:
                return await self._handle_stream_response(response)
            else:
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _custom_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        stream: bool,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """自定义/本地模型调用"""
        session = await self._get_session()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"自定义API错误: {error_text}")
            
            if stream:
                return await self._handle_stream_response(response)
            else:
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _handle_stream_response(self, response) -> str:
        """处理流式响应"""
        full_content = ""
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                json_str = line[6:]
                if json_str == '[DONE]':
                    break
                try:
                    chunk = json.loads(json_str)
                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    full_content += content
                except json.JSONDecodeError:
                    pass
        return full_content
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class MultiLLMClient:
    """
    多LLM客户端管理器
    
    支持同时使用多个LLM提供商和Agent级别的模型选择
    """
    
    def __init__(self, registry: Optional[AgentModelRegistry] = None):
        self.clients: Dict[str, LLMClient] = {}
        self.default_client: Optional[str] = None
        self.registry = registry or get_model_registry()
    
    def add_client(
        self, 
        name: str, 
        client: LLMClient, 
        is_default: bool = False,
        provider: Optional[str] = None
    ):
        """添加客户端"""
        self.clients[name] = client
        if is_default or self.default_client is None:
            self.default_client = name
        
        # 同时注册到模型注册表
        if provider:
            self.registry.register_model(name, ModelInfo(
                provider=provider,
                model_name=name,
                api_key=client.config.api_key,
                base_url=client.config.base_url
            ))
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        client_name: Optional[str] = None,
        agent_role: Optional[str] = None,
        task_type: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        使用指定客户端或根据Agent角色完成生成
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            client_name: 直接指定客户端名称
            agent_role: Agent角色（自动选择合适的模型）
            task_type: 任务类型
            stream: 是否流式输出
            **kwargs: 其他参数传递给LLM
            
        Returns:
            生成的文本
        """
        # 如果直接指定了客户端，使用该客户端
        if client_name:
            if client_name not in self.clients:
                raise ValueError(f"客户端不存在: {client_name}")
            return await self.clients[client_name].complete(
                prompt, system_prompt, stream, **kwargs
            )
        
        # 如果指定了Agent角色，从注册表获取合适的模型
        if agent_role:
            model_info = self.registry.get_model_for_agent(agent_role, task_type)
            if model_info:
                client = self.clients.get(model_info.provider)
                if client:
                    return await client.complete(
                        prompt, system_prompt, stream,
                        model=model_info.model_name,
                        **kwargs
                    )
        
        # 使用默认客户端
        if self.default_client:
            return await self.clients[self.default_client].complete(
                prompt, system_prompt, stream, **kwargs
            )
        
        raise ValueError("没有可用的LLM客户端")
    
    async def complete_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        agent_role: Optional[str] = None,
        task_type: Optional[str] = None,
        max_retries: int = 3,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        使用备用机制完成生成
        
        如果主模型失败，自动尝试备用模型
        """
        config = self.registry.get_agent_config(agent_role) if agent_role else None
        retry_count = 0
        
        # 获取模型列表
        if config:
            models_to_try = [config.primary_model] + config.fallback_models
        elif agent_role:
            model_info = self.registry.get_model_for_agent(agent_role, task_type)
            models_to_try = [model_info.model_name] if model_info else ["gpt-4"]
        else:
            models_to_try = list(self.clients.keys())
        
        last_error = None
        for model_id in models_to_try:
            if retry_count >= max_retries:
                break
            
            try:
                # 找到对应的客户端
                for client_name, client in self.clients.items():
                    if model_id.startswith(client_name) or client_name.startswith(model_id.split('-')[0]):
                        return await client.complete(
                            prompt, system_prompt, stream,
                            model=model_id, **kwargs
                        )
                
                # 直接使用默认客户端尝试该模型
                if self.default_client:
                    return await self.clients[self.default_client].complete(
                        prompt, system_prompt, stream,
                        model=model_id, **kwargs
                    )
                    
            except Exception as e:
                last_error = e
                retry_count += 1
                continue
        
        raise last_error or Exception("所有模型都失败了")
    
    async def close_all(self):
        """关闭所有客户端"""
        for client in self.clients.values():
            await client.close()
    
    def get_available_providers(self) -> List[str]:
        """获取所有可用的提供商"""
        return list(self.clients.keys())


def create_multi_client_from_config(
    config_path: str,
    api_keys: Optional[Dict[str, str]] = None
) -> MultiLLMClient:
    """
    从配置文件创建多LLM客户端
    
    Args:
        config_path: 配置文件路径
        api_keys: API密钥字典 {"provider": "key"}
        
    Returns:
        配置好的MultiLLMClient
    """
    import os
    
    # 初始化注册表并加载配置
    registry = get_model_registry()
    registry.load_from_yaml(config_path)
    
    # 创建多客户端
    multi_client = MultiLLMClient(registry)
    
    # 获取需要的环境变量前缀
    env_prefixes = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    
    # 为每个注册的模型创建客户端
    for model_id, model_info in registry.available_models.items():
        # 获取API密钥
        api_key = None
        if api_keys and model_info.provider in api_keys:
            api_key = api_keys[model_info.provider]
        else:
            # 尝试从环境变量获取
            env_var = env_prefixes.get(model_info.provider)
            if env_var:
                api_key = os.getenv(env_var)
        
        if api_key:
            config = LLMConfig(
                provider=LLMProvider(model_info.provider),
                api_key=api_key,
                base_url=model_info.base_url,
                model=model_info.model_name,
                temperature=model_info.temperature,
                max_tokens=model_info.max_tokens
            )
            client = LLMClient(config)
            
            # 检查是否是默认模型
            is_default = model_info.cost_tier == "medium"
            multi_client.add_client(
                model_info.provider, 
                client,
                is_default=is_default,
                provider=model_info.provider
            )
    
    return multi_client
