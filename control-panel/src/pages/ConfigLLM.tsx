import { Button, Card, Divider, Form, Input, InputNumber, message, Space, Switch, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigLLM() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string>(''); // 测试结果状态
  const [showApiKey, setShowApiKey] = useState(true); // 默认显示明文密钥
  
  useEffect(() => {
    console.log('ConfigLLM component mounted, loading config...');
    const loadConfig = async () => {
      try {
        console.log('Calling configApi.getLLM()...');
        const r = await configApi.getLLM();
        console.log('API response received:', r);
        const d = r.data.data as unknown as Record<string, unknown> || {};
        console.log('Config data:', d);
        
        if (d.api_key) {
          console.log('API Key from API:', d.api_key);
          console.log('API Key type:', typeof d.api_key);
          console.log('API Key length:', (d.api_key as string).length);
        }
        
        // 设置默认值
        const parameters = d.parameters as Record<string, unknown> || {};
        
        form.setFieldsValue({
          base_url: d.base_url,
          api_key: d.api_key,
          model: d.model,
          temperature: parameters.temperature !== undefined ? parameters.temperature : 0.2,
          max_tokens: parameters.max_tokens !== undefined ? parameters.max_tokens : 1024,
          top_p: parameters.top_p !== undefined ? parameters.top_p : 0.9,
          stream: parameters.stream !== undefined ? parameters.stream : false,
          seed: parameters.seed !== undefined ? parameters.seed : null,
          presence_penalty: parameters.presence_penalty !== undefined ? parameters.presence_penalty : 0,
          frequency_penalty: parameters.frequency_penalty !== undefined ? parameters.frequency_penalty : 0,
          n: parameters.n !== undefined ? parameters.n : 1,
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
        console.error('Failed to load LLM config:', error);
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      await configApi.updateLLM({
        base_url: values.base_url as string,
        api_key: values.api_key as string,
        model: values.model as string,
        parameters: {
          temperature: values.temperature as number,
          max_tokens: values.max_tokens as number,
          top_p: values.top_p as number,
          stream: values.stream as boolean,
          seed: values.seed as number | undefined,
          presence_penalty: values.presence_penalty as number,
          frequency_penalty: values.frequency_penalty as number,
          n: values.n as number,
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
    if (!values.base_url || !values.api_key || !values.model) {
      message.warning('请先填写 Base URL、API Key 和 Model');
      return;
    }
    setTesting(true);
    setTestResult(''); // 清空之前的测试结果
    try {
      const { data } = await configApi.validateLLM({
        base_url: values.base_url as string,
        api_key: values.api_key as string,
        model: values.model as string,
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
    <Card title="LLM 配置">
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
    <Form.Item name="model" label="Model" rules={[{ required: true }]}>
    <Input placeholder="qwen-turbo" />
    </Form.Item>
    <Form.Item name="temperature" label="Temperature">
    <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
    </Form.Item>
    <Form.Item name="max_tokens" label="Max Tokens">
    <InputNumber min={1} max={4096} style={{ width: '100%' }} />
    </Form.Item>
    <Form.Item name="top_p" label="Top P">
    <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
    </Form.Item>
    
    <Divider orientation="left">高级参数</Divider>
    
    <Form.Item name="stream" label="流式响应" valuePropName="checked">
    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
    </Form.Item>
    
    <Form.Item name="seed" label="随机种子">
    <InputNumber min={0} max={999999} placeholder="用于可复现性" style={{ width: '100%' }} />
    </Form.Item>
    
    <Form.Item name="presence_penalty" label="存在惩罚">
    <InputNumber min={-2} max={2} step={0.1} placeholder="-2.0到2.0" style={{ width: '100%' }} />
    </Form.Item>
    
    <Form.Item name="frequency_penalty" label="频率惩罚">
    <InputNumber min={-2} max={2} step={0.1} placeholder="-2.0到2.0" style={{ width: '100%' }} />
    </Form.Item>
    
    <Form.Item name="n" label="生成选项数">
    <InputNumber min={1} max={5} defaultValue={1} placeholder="1-5" style={{ width: '100%' }} />
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