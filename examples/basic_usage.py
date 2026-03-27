"""
多Agent协作写小说系统 - 基础使用示例

本示例演示如何：
1. 创建LLM客户端
2. 创建Agent编排器
3. 创建小说项目
4. 学习作家风格
5. 协作撰写章节
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.llm_client import LLMClient, LLMConfig, LLMProvider
from app.services.style_service import StyleService
from app.core.orchestrator import AgentOrchestrator
from app.agents.writer_agent import WriterAgent


async def demo_create_writer_style():
    """演示：从文本创建作家风格"""
    print("=" * 60)
    print("演示：创建作家风格")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",  # 替换为实际API Key
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建风格服务
    style_service = StyleService()
    
    # 样本文本（实际使用时可以上传文件）
    sample_texts = [
        """
        风清扬微微一笑，道："你倒也有趣。我这剑法，名为独孤九剑，
        乃是前辈高人独孤求败所创。这剑法讲究的是悟性，不是招式。
        你若能悟透其中奥妙，天下剑法，皆可破得。"
        """,
        """
        令狐冲心中一凛，暗想："这位前辈剑法通神，我若能学得一二，
        也不枉了这次奇遇。"当下恭恭敬敬地拜倒在地，道："弟子令狐冲，
        恳请前辈传授剑法。"
        """
    ]
    
    # 分析风格
    style = await style_service.analyze_style(
        name="金庸武侠风格",
        sample_texts=sample_texts,
        llm_client=llm_client,
        description="金庸武侠小说的经典写作风格"
    )
    
    print(f"\n风格名称: {style.name}")
    print(f"风格描述: {style.description}")
    print(f"\n词汇特征:")
    for feature in style.vocabulary_features:
        print(f"  - {feature}")
    
    print(f"\n句式特点:")
    for pattern in style.sentence_patterns:
        print(f"  - {pattern}")
    
    await llm_client.close()
    return style


async def demo_create_novel_project():
    """演示：创建小说项目"""
    print("\n" + "=" * 60)
    print("演示：创建小说项目")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建项目
    result = await orchestrator.create_novel_project(
        project_id="demo_project_001",
        title="星际武侠传",
        genre="科幻武侠",
        user_input="""
        我想写一部科幻武侠小说，故事发生在未来的星际时代。
        主角是一个来自偏远星球的年轻人，偶然获得了一本古老的武学秘籍。
        他要在星际之间冒险，对抗邪恶的星际帝国。
        希望融合武侠的浪漫和科幻的宏大。
        """,
        target_chapters=20
    )
    
    print(f"\n项目创建成功!")
    print(f"项目ID: {result['project_id']}")
    print(f"项目名称: {result['outline'].get('story_summary', 'N/A')[:100]}...")
    
    # 获取项目状态
    status = orchestrator.get_project_status("demo_project_001")
    print(f"\n项目状态:")
    print(f"  - 总章节: {status['total_chapters']}")
    print(f"  - 已完成: {status['completed_chapters']}")
    print(f"  - Agent数量: {len(status['agents'])}")
    
    await llm_client.close()
    return orchestrator


async def demo_mix_styles():
    """演示：混合多种风格"""
    print("\n" + "=" * 60)
    print("演示：混合作家风格")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建风格服务
    style_service = StyleService()
    
    # 假设已有两种风格
    # 实际使用时需要先创建这些风格
    try:
        mixed_style = await style_service.mix_styles(
            style_names=["金庸武侠风格", "刘慈欣科幻风格"],
            mix_name="科幻武侠混合风格",
            proportions=[0.6, 0.4],
            llm_client=llm_client
        )
        
        print(f"\n混合风格创建成功!")
        print(f"风格名称: {mixed_style.name}")
        print(f"风格描述: {mixed_style.description}")
        print(f"\n词汇特征:")
        for feature in mixed_style.vocabulary_features:
            print(f"  - {feature}")
            
    except ValueError as e:
        print(f"\n混合风格需要先创建基础风格: {e}")
    
    await llm_client.close()


async def demo_agent_collaboration():
    """演示：Agent协作写作"""
    print("\n" + "=" * 60)
    print("演示：Agent协作写作")
    print("=" * 60)
    
    # 创建LLM客户端
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )
    llm_client = LLMClient(config)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(llm_client)
    
    # 创建项目
    await orchestrator.create_novel_project(
        project_id="collab_demo",
        title="测试项目",
        genre="奇幻",
        user_input="一个关于魔法学院的青春成长故事",
        target_chapters=5
    )
    
    # 撰写第一章
    print("\n开始撰写第一章...")
    # 注意：实际调用需要有效的API Key
    # result = await orchestrator.write_chapter(
    #     project_id="collab_demo",
    #     chapter_num=1
    # )
    # print(f"第一章完成，字数: {result.get('word_count', 0)}")
    
    print("\n协作流程:")
    print("  1. 首席规划师协调各Agent")
    print("  2. 世界构建师提供世界观背景")
    print("  3. 角色设计师提供角色信息")
    print("  4. 主笔作家撰写内容")
    print("  5. 风格编辑润色")
    print("  6. 审核员质量检查")
    
    await llm_client.close()


async def main():
    """主函数"""
    print("多Agent协作写小说系统 - 基础使用示例")
    print("=" * 60)
    
    # 演示1: 创建作家风格
    # await demo_create_writer_style()
    
    # 演示2: 创建小说项目
    # await demo_create_novel_project()
    
    # 演示3: 混合风格
    # await demo_mix_styles()
    
    # 演示4: Agent协作
    await demo_agent_collaboration()
    
    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)
    print("\n注意：实际运行需要配置有效的API Key")
    print("请修改代码中的 'your-api-key' 为实际的API Key")


if __name__ == "__main__":
    asyncio.run(main())
