import { Card, Descriptions, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function Dashboard() {
  const [llmConfig, setLlmConfig] = useState<Record<string, unknown>>({});

  useEffect(() => {
    configApi.getLLM().then((r) => setLlmConfig(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <Typography.Title level={4}>系统概览</Typography.Title>
      
      <Card title="LLM 配置" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="Base URL">{String(llmConfig.base_url ?? '-')}</Descriptions.Item>
          <Descriptions.Item label="Model">{String(llmConfig.model ?? '-')}</Descriptions.Item>
          <Descriptions.Item label="温度">{String((llmConfig.parameters as Record<string, number>)?.temperature ?? '-')}</Descriptions.Item>
          <Descriptions.Item label="最大Token">{String((llmConfig.parameters as Record<string, number>)?.max_tokens ?? '-')}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}