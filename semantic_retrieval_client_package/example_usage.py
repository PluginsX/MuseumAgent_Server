"""语义检索客户端库使用示例"""

from semantic_retrieval_client import SemanticRetrievalClient
from semantic_retrieval_client.models import ArtifactCreate, ArtifactUpdate, SearchRequest
from semantic_retrieval_client.exceptions import APIError, ConnectionError, TimeoutError


def example_usage():
    """使用示例"""
    print("=== 语义检索客户端库使用示例 ===\n")
    
    # 创建客户端实例
    client = SemanticRetrievalClient(
        base_url="http://localhost:8080/api/v1",
        api_key="your-api-key-here",  # 可选
        timeout=300  # 请求超时时间（秒）
    )
    
    print("1. 客户端创建成功\n")
    
    # 示例：创建新资料
    print("2. 创建新资料示例:")
    try:
        new_artifact = ArtifactCreate(
            title="青铜器的历史",
            content="青铜器是中国古代文明的重要组成部分，具有很高的历史价值...",
            category="文物知识",
            tags=["青铜器", "文物", "历史"]
        )
        
        # 注意：实际调用需要服务器运行
        # created = client.create_artifact(new_artifact)
        print(f"   准备创建资料: {new_artifact.title}")
        print("   (需要服务器运行才能实际执行)\n")
    except Exception as e:
        print(f"   创建资料出错: {e}\n")
    
    # 示例：执行搜索
    print("3. 执行搜索示例:")
    try:
        search_result = client.search(
            query="青铜器的历史",
            top_k=5,
            threshold=0.7,
            category_filter=["文物知识"]
        )
        print(f"   搜索查询: {search_result.query}")
        print(f"   找到 {search_result.total_count} 条结果")
        print("   (需要服务器运行才能实际执行)\n")
    except Exception as e:
        print(f"   搜索出错: {e}\n")
    
    # 示例：异常处理
    print("4. 异常处理示例:")
    try:
        # 这里模拟一个可能的错误
        raise APIError(404, "资源未找到", {"resource": "artifact", "id": 123})
    except APIError as e:
        print(f"   捕获到API错误: {e.message}")
        print(f"   状态码: {e.status_code}")
    except ConnectionError as e:
        print(f"   连接错误: {e}")
    except TimeoutError as e:
        print(f"   超时错误: {e}")
    
    print("\n=== 使用示例结束 ===")


if __name__ == "__main__":
    example_usage()