import { Button, Card, Form, Input, message, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigEmbedding() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string>(''); // 测试结果状态
  const [showApiKey, setShowApiKey] = useState(true); // 默认显示明文密钥

  useEffect(() => {
    console.log('ConfigEmbedding component mounted, loading config...');
    const loadConfig = async () => {
      try {
        console.log('Calling configApi.getEmbedding()...');
        const r = await configApi.getEmbedding();
        console.log('API response received:', r);
        const d = r.data as Record<string, unknown>;
        console.log('Config data:', d);
        
        if (d.api_key) {
          console.log('API Key from API:', d.api_key);
          console.log('API Key type:', typeof d.api_key);
          console.log('API Key length:', (d.api_key as string).length);
        }
        
        form.setFieldsValue({
          base_url: d.base_url,
          api_key: d.api_key,
          model: d.model,
        });
        
        // 验证表单值是否设置成功
        setTimeout(() => {
          const formValues = form.getFieldsValue();
          console.log('Form values after setting:', formValues);
          if (formValues.api_key) {
            console.log('API Key in form:', formValues.api_key);
          }
        }, 100);
        
      } catch (error) {
        console.error('Failed to load Embedding config:', error);
      }
    };
    
    loadConfig();
  }, [form]);

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      await configApi.updateEmbedding({
        base_url: values.base_url,
        api_key: values.api_key,
        model: values.model,
      });
      message.success('保存成功，重启服务后生效');
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    const values = form.getFieldsValue();
    if (!values.base_url || !values.api_key || !values.model) {
      message.warning('请先填写 Base URL、API Key 和 Model');
      return;
    }
    setTesting(true);
    setTestResult(''); // 清空之前的测试结果
    try {
      const { data } = await configApi.testEmbedding({
        base_url: values.base_url,
        api_key: values.api_key,
        model: values.model,
        test_text: '测试文本',
      });
      const result = (data as { valid?: boolean; message?: string });
      setTestResult(result.message || '连接成功');
      message.success(result.message || '连接成功');
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } };
      const errorMsg = err.response?.data?.message || '连接失败';
      setTestResult(errorMsg);
      message.error(errorMsg);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div>
      <Card title="Embedding 配置">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
            <Input placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Input 
                type={showApiKey ? "text" : "password"}
                placeholder="请输入完整的API Key"
                autoComplete="off"
                spellCheck="false"
                style={{
                  flexGrow: 1,
                  backgroundColor: '#1a1a1a',
                  borderColor: '#333333',
                  color: '#ffffff',
                }}
              />
              <Button 
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? '隐藏' : '显示'}
              </Button>
              <Button 
                onClick={() => {
                  const value = form.getFieldValue('api_key');
                  if (value) {
                    navigator.clipboard.writeText(value as string);
                    message.success('已复制到剪贴板');
                  }
                }}
              >
                复制
              </Button>
            </div>
          </Form.Item>
          <Form.Item name="model" label="Model" rules={[{ required: true }]}>
            <Input placeholder="text-embedding-v4" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存
              </Button>
              <Button onClick={testConnection} loading={testing}>
                测试连接
              </Button>
              {testResult && (
                <Typography.Text type={testResult.includes('成功') || testResult.includes('valid') ? 'success' : 'danger'}>
                  {testResult}
                </Typography.Text>
              )}
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}