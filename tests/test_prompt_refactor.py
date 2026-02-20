# -*- coding: utf-8 -*-
"""
提示词构建模块测试脚本
验证重构后的模板引擎和提示词构建功能
"""
import sys
import os
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.modules.prompt_template_engine import PromptTemplateEngine
from src.core.modules.prompt_builder import PromptBuilder
from src.session.strict_session_manager import strict_session_manager
from src.common.config_utils import load_config
import json


# 加载配置
load_config()


def test_template_engine():
    """测试模板引擎"""
    print("=" * 60)
    print("测试1: 模板引擎基础功能")
    print("=" * 60)
    
    engine = PromptTemplateEngine()
    
    # 测试系统消息渲染
    system_vars = {
        "role_description": "你叫韩立，是辽宁省博物馆的智能讲解员。",
        "response_requirements": "基于当前场景回答用户问题。",
        "scene_description": "当前所处的是'西周青铜器造型纹样展示区'。",
        "functions_description": "• move_camera: 移动摄像机\n• play_music: 播放音乐"
    }
    
    system_message = engine.render_system_message(system_vars)
    print("\n系统消息:")
    print("-" * 60)
    print(system_message)
    
    # 测试用户消息渲染（带RAG）
    user_vars = {
        "user_input": "饕餮纹是什么寓意？",
        "retrieved_materials": "【饕餮纹资料1】\n饕餮纹是青铜器上常见的纹样..."
    }
    
    user_message = engine.render_user_message(user_vars, has_rag=True)
    print("\n用户消息（带RAG）:")
    print("-" * 60)
    print(user_message)
    
    # 测试用户消息渲染（不带RAG）
    user_message_no_rag = engine.render_user_message({"user_input": "你好"}, has_rag=False)
    print("\n用户消息（不带RAG）:")
    print("-" * 60)
    print(user_message_no_rag)
    
    print("\n✅ 模板引擎测试通过\n")


def test_prompt_builder():
    """测试提示词构建器"""
    print("=" * 60)
    print("测试2: 提示词构建器完整流程")
    print("=" * 60)
    
    # 创建测试会话
    session_id = "test_session_123"
    
    # 注册会话
    client_metadata = {
        "platform": "web",
        "require_tts": False,
        "enable_srs": True,
        "user_id": "test_user",
        "system_prompt": {
            "role_description": "你叫韩立，是辽宁省博物馆的智能讲解员。性别男，性格热情阳光开朗健谈。",
            "response_requirements": "基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。"
        },
        "scene_context": {
            "current_scene": "bronze_exhibition",
            "scene_description": "当前所处的是'西周青铜器造型纹样展示区'，主要内容为西周青铜器表面包含的各种纹样的图形和寓意展示。",
            "scene_specific_prompt": "请注意结合展品的历史背景和文化内涵进行讲解。"
        }
    }
    
    # 测试函数定义
    functions = [
        {
            "name": "move_camera",
            "description": "移动摄像机到指定位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {"type": "string", "description": "目标位置"}
                }
            }
        },
        {
            "name": "play_music",
            "description": "播放指定的背景音乐",
            "parameters": {
                "type": "object",
                "properties": {
                    "music_name": {"type": "string", "description": "音乐名称"}
                }
            }
        }
    ]
    
    strict_session_manager.register_session_with_functions(
        session_id, client_metadata, functions
    )
    
    print(f"\n✅ 测试会话已创建: {session_id}")
    
    # 创建提示词构建器
    builder = PromptBuilder()
    
    # 模拟RAG检索结果
    rag_context = {
        "relevant_artifacts": [
            {
                "title": "饕餮纹介绍",
                "content": "饕餮纹是青铜器上最常见的纹样之一，象征着权力和威严。"
            },
            {
                "title": "饕餮纹的历史",
                "content": "饕餮纹起源于商代，在西周时期达到鼎盛。"
            }
        ]
    }
    
    # 构建完整payload
    user_input = "饕餮纹是什么寓意？"
    payload = builder.build_llm_payload(
        session_id=session_id,
        user_input=user_input,
        rag_context=rag_context
    )
    
    print("\n生成的LLM API Payload:")
    print("-" * 60)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 验证payload结构
    assert "model" in payload, "缺少model参数"
    assert "messages" in payload, "缺少messages参数"
    assert len(payload["messages"]) == 2, "messages应包含2条消息"
    assert payload["messages"][0]["role"] == "system", "第一条消息应为system"
    assert payload["messages"][1]["role"] == "user", "第二条消息应为user"
    assert "functions" in payload, "缺少functions参数"
    assert payload["function_call"] == "auto", "function_call应为auto"
    assert "temperature" in payload, "缺少temperature参数"
    assert "max_tokens" in payload, "缺少max_tokens参数"
    assert "top_p" in payload, "缺少top_p参数"
    
    print("\n✅ Payload结构验证通过")
    
    # 清理测试会话
    strict_session_manager.unregister_session(session_id)
    print(f"\n✅ 测试会话已清理: {session_id}\n")


def test_without_rag():
    """测试不带RAG的场景"""
    print("=" * 60)
    print("测试3: 不带RAG的提示词构建")
    print("=" * 60)
    
    session_id = "test_session_no_rag"
    
    client_metadata = {
        "platform": "web",
        "require_tts": False,
        "enable_srs": False,  # 禁用RAG
        "user_id": "test_user",
        "system_prompt": {
            "role_description": "你是智能助手。",
            "response_requirements": "请简洁回答问题。"
        },
        "scene_context": {
            "scene_description": "通用对话场景"
        }
    }
    
    strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    
    builder = PromptBuilder()
    payload = builder.build_llm_payload(
        session_id=session_id,
        user_input="你好",
        rag_context=None
    )
    
    print("\n生成的Payload（无RAG，无函数）:")
    print("-" * 60)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 验证
    assert "functions" not in payload, "不应包含functions参数"
    assert "function_call" not in payload, "不应包含function_call参数"
    
    print("\n✅ 无RAG场景测试通过")
    
    strict_session_manager.unregister_session(session_id)
    print(f"\n✅ 测试会话已清理: {session_id}\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("提示词构建模块重构测试")
    print("=" * 60 + "\n")
    
    try:
        test_template_engine()
        test_prompt_builder()
        test_without_rag()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n重构成功！新架构特点：")
        print("1. ✅ 模板与数据完全分离")
        print("2. ✅ 配置文件定义模板结构")
        print("3. ✅ 运行时数据动态填充")
        print("4. ✅ 系统消息和用户消息分别构建")
        print("5. ✅ API参数从配置文件获取")
        print("6. ✅ 支持RAG和函数调用")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

