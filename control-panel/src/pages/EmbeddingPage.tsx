import { Button, Card, Descriptions, Input, message, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { embeddingApi } from '../api/client';

const { TextArea } = Input;

export default function EmbeddingPage() {
  // 使用localStorage来持久化数据
  const [text, setText] = useState(() => {
    return localStorage.getItem('embedding-text') || '';
  });
  const [artifactId, setArtifactId] = useState(() => {
    return localStorage.getItem('embedding-artifact-id') || '';
  });
  const [artifactName, setArtifactName] = useState(() => {
    return localStorage.getItem('embedding-artifact-name') || '';
  });
  const [vectorData, setVectorData] = useState(() => {
    return localStorage.getItem('embedding-vector-data') || '';
  });
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    dimension?: number;
    processing_time?: number;
    vector?: number[];
  } | null>(null);
  const [searchText, setSearchText] = useState('');
  const [searchResult, setSearchResult] = useState<Array<{ id?: string; document?: string; metadata?: Record<string, string> }> | []>([]);
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState<{ total_vectors?: number }>({total_vectors: 0});

  // 监听状态变化并保存到localStorage
  useEffect(() => {
    localStorage.setItem('embedding-text', text);
  }, [text]);

  useEffect(() => {
    localStorage.setItem('embedding-artifact-id', artifactId);
  }, [artifactId]);

  useEffect(() => {
    localStorage.setItem('embedding-artifact-name', artifactName);
  }, [artifactName]);

  useEffect(() => {
    localStorage.setItem('embedding-vector-data', vectorData);
  }, [vectorData]);

  const loadStats = () => {
    console.log('Loading stats...');
    embeddingApi.stats()
      .then((r) => {
        console.log('Stats API response:', r);
        console.log('Stats data:', r.data);
        console.log('Total vectors from API:', r.data.total_vectors);
        setStats(r.data);
        console.log('Stats state after update:', r.data);
      })
      .catch((error) => {
        console.error('Stats API error:', error);
      });
  };

  const vectorize = async () => {
    if (!text.trim()) {
      message.warning('请输入文本');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const { data } = await embeddingApi.vectorize({
        text: text.trim(),
        artifact_id: artifactId || undefined,
      });
      setResult(data as { dimension?: number; processing_time?: number; vector?: number[] });
      
      // 将向量结果转换为字符串并填入向量数据框
      const vectorStr = JSON.stringify((data as any).vector || []);
      setVectorData(vectorStr);
      
      message.success('向量化成功！');
    } catch (e: unknown) {
      console.error('向量化错误:', e);
      const err = e as { 
        response?: { 
          data?: { 
            detail?: string;
            message?: string;
          } 
        } 
      };
      
      // 提取错误信息，优先使用 detail，其次使用 message，最后使用默认值
      const errorMsg = err.response?.data?.detail || 
                     err.response?.data?.message || 
                     '向量化失败';
      
      // 判断是否为格式错误，提供更友好的提示
      if (errorMsg.includes('格式错误') || errorMsg.includes('格式') || errorMsg.includes('OpenAI')) {
        message.error({
          content: '向量化失败',
          description: errorMsg,
          duration: 8,
        });
      } else {
        message.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const storeVector = async () => {
    if (!text.trim() && !vectorData.trim()) {
      message.warning('请输入文本或向量数据');
      return;
    }
    
    setLoading(true);
    try {
      // 如果有向量数据，直接使用向量数据存储
      if (vectorData.trim()) {
        // 尝试解析向量数据
        let vectorArray;
        try {
          vectorArray = JSON.parse(vectorData.trim());
          if (!Array.isArray(vectorArray) || vectorArray.length === 0) {
            throw new Error('向量数据格式不正确');
          }
        } catch (e) {
          message.error('向量数据格式不正确，请输入有效的JSON数组');
          return;
        }

        // 这里需要后端API支持直接存储向量数据
        // 临时使用文本存储功能
        await embeddingApi.store({
          artifact_id: artifactId.trim(),
          text_content: text.trim() || 'Custom Vector Data',
          artifact_name: artifactName.trim() || artifactId.trim() || 'Custom Vector',
        });
      } else {
        // 使用文本内容存储
        await embeddingApi.store({
          artifact_id: artifactId.trim(),
          text_content: text.trim(),
          artifact_name: artifactName.trim() || artifactId.trim(),
        });
      }
      
      message.success('已加入向量库');
      loadStats();
      
      // 清空向量数据框，但保留文本内容
      setVectorData('');
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail || '存储失败');
    } finally {
      setLoading(false);
    }
  };

  const search = async () => {
    if (!searchText.trim()) {
      message.warning('请输入查询文本');
      return;
    }
    setSearching(true);
    try {
      const { data } = await embeddingApi.search({ query_text: searchText.trim(), top_k: 5 });
      setSearchResult((data as { results?: Array<{ id?: string; document?: string; metadata?: Record<string, string> }> }).results || []);
    } catch (e: unknown) {
      message.error('搜索失败');
    } finally {
      setSearching(false);
    }
  };

  // 页面加载时获取统计数据
  useEffect(() => {
    console.log('Component mounted, loading stats...');
    // 延迟加载确保认证完成
    const timer = setTimeout(() => {
      loadStats();
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <div>
      {/* 第一部分：自然语言文本输入 */}
      <Typography.Title level={5}>向量化</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="文物 ID（可选）" value={artifactId} onChange={(e) => setArtifactId(e.target.value)} />
          <Input placeholder="文物名称（可选）" value={artifactName} onChange={(e) => setArtifactName(e.target.value)} />
          <TextArea
            placeholder="请输入文物描述文本..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
          />
          <Space>
            <Button type="primary" onClick={vectorize} loading={loading}>
              转为向量
            </Button>
            <Button onClick={storeVector} loading={loading}>
              加入向量库
            </Button>
          </Space>
        </Space>
        {result && (
          <Descriptions column={1} style={{ marginTop: 16 }}>
            <Descriptions.Item label="维度">{result.dimension}</Descriptions.Item>
            <Descriptions.Item label="处理时间">{result.processing_time} s</Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      {/* 第二部分：向量数据输入 */}
      <Typography.Title level={5}>向量数据</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <TextArea
            placeholder="直接粘贴向量数据 (JSON 数组格式，例如: [0.1, 0.2, 0.3, ...])"
            value={vectorData}
            onChange={(e) => setVectorData(e.target.value)}
            rows={4}
          />
          <Space>
            <Button type="primary" onClick={storeVector} loading={loading}>
              加入向量库
            </Button>
          </Space>
        </Space>
      </Card>

      {/* 第三部分：向量搜索与统计 */}
      <Typography.Title level={5}>向量搜索</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="输入查询文本"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onPressEnter={search}
          />
          <Button type="primary" onClick={search} loading={searching}>
            搜索
          </Button>
        </Space.Compact>
        {searchResult.length > 0 && (
          <div style={{ marginTop: 16 }}>
            {searchResult.map((item, i) => (
              <Card key={item.id || i} size="small" style={{ marginTop: 8 }}>
                <p>{item.document}</p>
                <Typography.Text type="secondary">{JSON.stringify(item.metadata)}</Typography.Text>
              </Card>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <Space>
          <Typography.Text>
            向量库数量: 
            <span style={{color: 'red', fontWeight: 'bold'}}> 
              {(() => {
                console.log('Rendering stats:', stats);
                console.log('Total vectors in state:', stats.total_vectors);
                return stats.total_vectors ?? 0;
              })()}
            </span>
          </Typography.Text>
          <Button size="small" onClick={loadStats}>
            刷新
          </Button>
        </Space>
      </Card>
    </div>
  );
}
