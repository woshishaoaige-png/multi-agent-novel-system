"""
多Agent协作写小说系统 - 高级使用示例

演示如何：
1. 使用Agent级别的模型配置
2. 从配置文件加载模型设置
3. 动态切换Agent模型
4. 使用模型回退机制
5. 获取模型使用统计
"""

import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.llm_client import LLMClient, LLMConfig, LLMProvider, create_multi_client_from_config
from app.services.style_service import StyleService
from app.core.orchestrator import AgentOrchestrator, WorkflowType
from app.agents.base_agent import AgentRole
from app.config.agent_model_config import (
    init_model_registry,
    get_model_registry,
    AgentModelRegistry,
    ModelInfo,
    ModelCapability
)


async def demo_basic_model_config():
    """演示1: 基础模型配置"""
    print("\n" + "=" * 60)
    print("演示1: 基础模型配置")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建Agent - 默认使用配置中的模型
    planner = orchestrator.create_agent(AgentRole.PLANNER, "my_planner")
    writer = orchestrator.create_agent(AgentRole.WRITER, "my_writer")
    
    print(f"Planner 使用模型: {orchestrator.get_agent_model(planner.agent_id)}")
    print(f"Writer 使用模型: {orchestrator.get_agent_model(writer.agent_id)}")
    
    await llm_client.close()


async def demo_custom_agent_models():
    """演示2: 为Agent指定自定义模型"""
    print("\n" + "=" * 60)
    print("演示2: 为Agent指定自定义模型")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 为不同Agent指定不同的模型
    planner = orchestrator.create_agent(
        AgentRole.PLANNER,
        "custom_planner",
        model_id="gpt-4"
    )
    
    writer = orchestrator.create_agent(
        AgentRole.WRITER,
        "custom_writer",
        model_id="claude-3-opus"
    )
    
    editor = orchestrator.create_agent(
        AgentRole.STYLE_EDITOR,
        "custom_editor",
        model_id="gpt-3.5-turbo"  # 使用更便宜的模型处理简单任务
    )
    
    print(f"Planner 使用模型: {orchestrator.get_agent_model(planner.agent_id)}")
    print(f"Writer 使用模型: {orchestrator.get_agent_model(writer.agent_id)}")
    print(f"Editor 使用模型: {orchestrator.get_agent_model(editor.agent_id)}")
    
    await llm_client.close()


async def demo_load_config_from_yaml():
    """演示3: 从YAML配置文件加载模型配置"""
    print("\n" + "=" * 60)
    print("演示3: 从YAML配置文件加载模型配置")
    print("=" * 60)
    
    # 初始化注册表并加载配置
    config_path = os.path.join(
        os.path.dirname(__file__),
        '../config/models_config.example.yaml'
    )
    
    if os.path.exists(config_path):
        registry = init_model_registry(config_path)
    else:
        registry = get_model_registry()
        # 手动注册一些模型
        registry.register_model("gpt-4", ModelInfo(
            provider="openai",
            model_name="gpt-4",
            capabilities=[ModelCapability.GENERAL, ModelCapability.CREATIVE],
            cost_tier="expensive",
            description="GPT-4"
        ))
    
    print("\n可用模型:")
    for model in registry.list_models():
        print(f"  - {model['model_id']}: {model['description']}")
    
    print("\nAgent模型配置:")
    for agent_config in registry.list_agent_configs():
        print(f"  - {agent_config['agent_role']}: {agent_config['primary_model']}")
    
    return registry


async def demo_multi_provider_setup():
    """演示4: 多提供商设置"""
    print("\n" + "=" * 60)
    print("演示4: 多提供商设置")
    print("=" * 60)
    
    # 从配置文件创建多客户端
    config_path = os.path.join(
        os.path.dirname(__file__),
        '../config/models_config.example.yaml'
    )
    
    if os.path.exists(config_path):
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY")
        }
        # 过滤掉None的key
        api_keys = {k: v for k, v in api_keys.items() if v}
        
        multi_client = create_multi_client_from_config(config_path, api_keys)
        
        print("已配置的提供商:")
        for provider in multi_client.get_available_providers():
            print(f"  - {provider}")
        
        return multi_client
    else:
        print("配置文件不存在，跳过多提供商演示")
        return None


async def demo_project_with_custom_models():
    """演示5: 使用自定义模型配置创建项目"""
    print("\n" + "=" * 60)
    print("演示5: 使用自定义模型配置创建项目")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 定义Agent模型配置
    agent_models = {
        "planner": "gpt-4",
        "world_builder": "gpt-4",
        "character_designer": "gpt-4",
        "writer": "gpt-4"
    }
    
    # 创建项目时指定模型配置
    # 注意：需要有效的API Key才能真正运行
    print("\n项目配置:")
    print(f"  - 项目ID: demo_custom_model_project")
    print(f"  - 标题: 测试项目")
    print(f"  - Agent模型配置:")
    for agent, model in agent_models.items():
        print(f"    * {agent}: {model}")
    
    # 打印项目状态结构
    print("\n项目状态结构:")
    print("  - project_id")
    print("  - title")
    print("  - agent_models_used: 使用的模型配置")
    print("  - agents: Agent列表")
    
    await llm_client.close()


async def demo_dynamic_model_switch():
    """演示6: 动态切换模型"""
    print("\n" + "=" * 60)
    print("演示6: 动态切换模型")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建Agent
    planner = orchestrator.create_agent(AgentRole.PLANNER, "dynamic_planner")
    
    print(f"初始模型: {orchestrator.get_agent_model(planner.agent_id)}")
    
    # 动态切换模型
    orchestrator.set_agent_model(planner.agent_id, "claude-3-opus")
    print(f"切换后模型: {orchestrator.get_agent_model(planner.agent_id)}")
    
    # 或者直接在Agent上切换
    planner.switch_model("gemini-pro")
    print(f"Agent直接切换后: {planner.model_id}")
    
    await llm_client.close()


async def demo_model_stats():
    """演示7: 获取模型使用统计"""
    print("\n" + "=" * 60)
    print("演示7: 获取模型使用统计")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建多个Agent
    orchestrator.create_agent(AgentRole.PLANNER, "stats_planner")
    orchestrator.create_agent(AgentRole.WRITER, "stats_writer")
    orchestrator.create_agent(AgentRole.EDITOR, "stats_editor")
    
    # 手动设置不同的模型
    orchestrator.set_agent_model("stats_planner", "gpt-4")
    orchestrator.set_agent_model("stats_writer", "claude-3-opus")
    orchestrator.set_agent_model("stats_editor", "gpt-3.5-turbo")
    
    # 获取统计
    stats = orchestrator.get_model_stats()
    
    print("\n模型使用统计:")
    print(f"  - 总Agent数量: {stats['total_agents']}")
    print(f"  - 模型使用分布:")
    for model, agents in stats['model_usage'].items():
        print(f"    * {model}: {', '.join(agents)}")
    
    print(f"  - 可用模型列表:")
    for model in stats['available_models']:
        print(f"    * {model['model_id']} ({model['provider']}): {model['description']}")
    
    await llm_client.close()


async def demo_workflow_with_models():
    """演示8: 工作流中的模型配置"""
    print("\n" + "=" * 60)
    print("演示8: 工作流中的模型配置")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建Agent
    planner = orchestrator.create_agent(AgentRole.PLANNER, "workflow_planner")
    world_builder = orchestrator.create_agent(AgentRole.WORLD_BUILDER, "workflow_world")
    
    # 创建工作流，指定任务级别的模型
    workflow = orchestrator.create_workflow(
        workflow_id="model_workflow",
        name="测试工作流",
        workflow_type=WorkflowType.SEQUENTIAL,
        project_id="test_project",
        tasks_config=[
            {
                "type": "create_outline",
                "agent_id": planner.agent_id,
                "params": {"user_input": "测试"},
                "model_id": "gpt-4"  # 指定模型
            },
            {
                "type": "create_world",
                "agent_id": world_builder.agent_id,
                "params": {"genre": "奇幻"},
                "model_id": "claude-3-opus"  # 指定不同模型
            }
        ]
    )
    
    print(f"工作流创建成功")
    print(f"  - 工作流ID: {workflow.workflow_id}")
    print(f"  - 任务数: {len(workflow.tasks)}")
    for i, task in enumerate(workflow.tasks):
        print(f"  - 任务{i+1}: agent={task.agent_id}, model={task.model_id}")
    
    await llm_client.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("多Agent协作写小说系统 - 高级使用示例")
    print("模型配置功能演示")
    print("=" * 60)
    
    # 演示1: 基础模型配置
    await demo_basic_model_config()
    
    # 演示2: 自定义Agent模型
    await demo_custom_agent_models()
    
    # 演示3: 从配置文件加载
    await demo_load_config_from_yaml()
    
    # 演示4: 多提供商设置
    await demo_multi_provider_setup()
    
    # 演示5: 自定义模型创建项目
    await demo_project_with_custom_models()
    
    # 演示6: 动态模型切换
    await demo_dynamic_model_switch()
    
    # 演示7: 模型使用统计
    await demo_model_stats()
    
    # 演示8: 工作流中的模型配置
    await demo_workflow_with_models()
    
    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)
    print("\n提示：实际运行需要配置有效的API Key")


if __name__ == "__main__":
    asyncio.run(main())
