"""语义检索客户端库的简单测试"""

def test_import():
    """测试能否成功导入库"""
    try:
        from semantic_retrieval_client import SemanticRetrievalClient
        from semantic_retrieval_client.models import Artifact, SearchRequest
        from semantic_retrieval_client.exceptions import APIError, ClientError
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_classes():
    """测试类是否可以正常实例化"""
    try:
        from semantic_retrieval_client import SemanticRetrievalClient
        from semantic_retrieval_client.models import ArtifactCreate
        
        # 尝试创建客户端实例
        client = SemanticRetrievalClient(base_url="http://test.local")
        print("✓ SemanticRetrievalClient 实例化成功")
        
        # 尝试创建模型实例
        artifact_create = ArtifactCreate(
            title="Test Title",
            content="Test Content",
            category="Test Category"
        )
        print("✓ ArtifactCreate 实例化成功")
        
        return True
    except Exception as e:
        print(f"✗ 实例化失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试 semantic-retrieval-client 包...")
    success = True
    
    success &= test_import()
    success &= test_classes()
    
    if success:
        print("\n✓ 所有测试通过！包结构正确。")
    else:
        print("\n✗ 测试未全部通过，请检查包结构。")