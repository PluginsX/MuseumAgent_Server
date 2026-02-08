import { Button, Card, Divider, Form, Input, InputNumber, message, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigSRS() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string>(''); // 测试结果状态
  const [showApiKey, setShowApiKey] = useState(true); // 默认显示明文密钥
  
  useEffect(() => {
    console.log('ConfigSRS component mounted, loading config...');
    const loadConfig = async () => {
      try {
        console.log('Calling configApi.getSRS()...');
        const r = await configApi.getSRS();
        console.log('API response received:', r);
        const d = r.data as Record<string, unknown>;
        console.log('Config data:', d);
        
        if (d.api_key) {
          console.log('API Key from API:', d.api_key);
          console.log('API Key type:', typeof d.api_key);
          console.log('API Key length:', (d.api_key as string).length);
        }
        
        // 设置默认值
        const searchParams = d.search_params as Record<string, number> || {};
        
        form.setFieldsValue({
          base_url: d.base_url,
          api_key: d.api_key,
          timeout: d.timeout !== undefined ? d.timeout : 300,
          top_k: searchParams.top_k !== undefined ? searchParams.top_k : 3,
          threshold: searchParams.threshold !== undefined ? searchParams.threshold : 0.7,
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
        console.error('Failed to load SRS config:', error);
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      await configApi.updateSRS({
        base_url: values.base_url,
        api_key: values.api_key,
        timeout: values.timeout,
        search_params: {
          top_k: values.top_k,
          threshold: values.threshold,
        },
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
    if (!values.base_url) {
      message.warning('请先填写 Base URL');
      return;
    }
    setTesting(true);
    setTestResult(''); // 清空之前的测试结果
    try {
      const { data } = await configApi.validateSRS({
        base_url: values.base_url,
        api_key: values.api_key || '',
      });
      const result = (data as { valid?: boolean; message?: string });
      setTestResult(result.message || '连接成功');
      if (result.valid) {
        message.success(result.message || '连接成功');
      } else {
        message.error(result.message || '连接失败');
      }
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
    <Card title="SRS配置">
    <Form form={form} layout="vertical" onFinish={onFinish}>
    <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
    <Input placeholder="http://localhost:12315/api/v1" />
    </Form.Item>
    <Form.Item name="api_key" label="API Key">
    <div style={{ display: 'flex', gap: '8px' }}>
    <Input 
    type={showApiKey ? "text" : "password"}
    placeholder="请输入API Key"
    autoComplete="off"
    spellCheck="false"
    style={{ flexGrow: 1 }}
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
    <Form.Item name="timeout" label="超时时间（秒）">
    <InputNumber min={10} max={600} step={10} style={{ width: '100%' }} />
    </Form.Item>
    <Divider orientation="left">搜索参数</Divider>
    <Form.Item name="top_k" label="最大资料数量">
    <InputNumber min={1} max={10} step={1} style={{ width: '100%' }} />
    </Form.Item>
    <Form.Item name="threshold" label="相似度阈值">
    <InputNumber min={0} max={1} step={0.05} style={{ width: '100%' }} />
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
