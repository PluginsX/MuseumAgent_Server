#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG模块诊断脚本
测试完整的向量化和检索流程
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置
from src.common.config_utils import load_config
load_config()

from src.core.chroma_service import ChromaService
from src.core.embedding_client import EmbeddingClient
from src.common.config_utils import get_global_config
from src.common.log_formatter import log_step, log_communication

def diagnose_embedding_config():
    """诊断Embedding配置"""
    print("=" * 80)
    print("🔧 Embedding配置诊断")
    print("=" * 80)
    
    try:
        config = get_global_config()
        emb_config = config.get("embedding", {})
        
        print(f"📊 配置信息:")
        print(f"  - Base URL: {emb_config.get('base_url', '未配置')}")
        print(f"  - API Key: {emb_config.get('api_key', '未配置')}")
        print(f"  - Model: {emb_config.get('model', '未配置')}")
        print(f"  - Dimensions: {emb_config.get('parameters', {}).get('dimensions', '未设置')}")
        
        # 检查必要配置
        missing_configs = []
        if not emb_config.get('base_url'):
            missing_configs.append('base_url')
        if not emb_config.get('api_key'):
            missing_configs.append('api_key')
        if not emb_config.get('model'):
            missing_configs.append('model')
            
        if missing_configs:
            print(f"\n❌ 缺失必要配置: {', '.join(missing_configs)}")
            print("💡 请在 config.json 的 embedding 部分配置相关信息")
            return False
        else:
            print("\n✅ Embedding配置完整")
            return True
            
    except Exception as e:
        print(f"\n❌ 配置读取失败: {str(e)}")
        return False

def test_embedding_api():
    """测试Embedding API调用"""
    print("\n" + "=" * 80)
    print("🧪 Embedding API测试")
    print("=" * 80)
    
    try:
        client = EmbeddingClient()
        test_text = "卷体夔纹蟠龙盖罍"
        
        print(f"📝 测试文本: {test_text}")
        print(f"🔄 调用Embedding API...")
        
        vectors = client.embed(test_text)
        vector = vectors[0] if vectors else []
        
        print(f"\n✅ 向量化成功!")
        print(f"  - 向量维度: {len(vector)}")
        print(f"  - 向量预览: [{vector[0]:.4f}, {vector[1]:.4f}, ... , {vector[-1]:.4f}]")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Embedding API调用失败: {str(e)}")
        return False

def test_chroma_service():
    """测试ChromaDB服务"""
    print("\n" + "=" * 80)
    print("🗄️ ChromaDB服务测试")
    print("=" * 80)
    
    try:
        service = ChromaService()
        
        # 检查数据库状态
        count = service.count()
        print(f"📊 向量库统计:")
        print(f"  - 总向量数: {count}")
        
        if count == 0:
            print("⚠️  向量库为空，建议添加测试数据")
            return True  # 不算失败，只是提醒
        
        # 测试搜索功能
        test_query = "蟠龙文物"
        print(f"\n🔍 测试搜索: '{test_query}'")
        
        results = service.search(query_text=test_query, top_k=3)
        print(f"✅ 搜索完成，找到 {len(results)} 个结果")
        
        for i, result in enumerate(results[:2]):  # 显示前2个结果
            print(f"  结果 {i+1}:")
            print(f"    - 文档: {result.get('document', '')[:100]}...")
            print(f"    - 距离: {result.get('distance', 'N/A')}")
            print(f"    - 元数据: {result.get('metadata', {})}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ChromaDB服务测试失败: {str(e)}")
        return False

def test_full_rag_pipeline():
    """测试完整的RAG流水线"""
    print("\n" + "=" * 80)
    print("🔗 完整RAG流水线测试")
    print("=" * 80)
    
    try:
        service = ChromaService()
        
        # 测试完整的检索流程
        user_query = "介绍一下蟠龙盖罍这件文物"
        print(f"🎯 用户查询: {user_query}")
        
        print("\n🔄 执行完整RAG流程...")
        results = service.search(query_text=user_query, top_k=2)
        
        print(f"\n✅ RAG流程执行成功!")
        print(f"  - 检索到 {len(results)} 个相关文档")
        
        if results:
            print("\n📄 检索结果详情:")
            for i, result in enumerate(results):
                print(f"  {i+1}. {result.get('document', '')[:150]}...")
                print(f"     相似度距离: {result.get('distance', 'N/A')}")
        else:
            print("  ⚠️ 未检索到相关文档")
            
        return True
        
    except Exception as e:
        print(f"\n❌ RAG流水线测试失败: {str(e)}")
        return False

def main():
    """主诊断函数"""
    print("🔍 博物馆智能体 RAG模块诊断工具")
    print("=" * 80)
    
    results = []
    
    # 1. 配置诊断
    config_ok = diagnose_embedding_config()
    results.append(("配置诊断", config_ok))
    
    if not config_ok:
        print("\n❌ 配置存在问题，跳过后续测试")
        return
    
    # 2. API测试
    api_ok = test_embedding_api()
    results.append(("API测试", api_ok))
    
    # 3. 数据库测试
    db_ok = test_chroma_service()
    results.append(("数据库测试", db_ok))
    
    # 4. 完整流程测试
    pipeline_ok = test_full_rag_pipeline()
    results.append(("完整流程", pipeline_ok))
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 诊断总结")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！RAG模块工作正常")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")

if __name__ == "__main__":
    main()