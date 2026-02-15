import { Button, Card, Divider, Form, Input, InputNumber, message, Space, Switch, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigSTT() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string>(''); // 测试结果状态
  const [showApiKey, setShowApiKey] = useState(true); // 默认显示明文密钥
  
  useEffect(() => {
    console.log('ConfigSTT component mounted, loading config...');
    const loadConfig = async () => {
      try {
        console.log('Calling configApi.getSTT()...');
        const r = await configApi.getSTT();
        console.log('API response received:', r);
        const d = r.data as Record<string, unknown>;
        console.log('Config data:', d);
        
        if (d.api_key) {
          console.log('API Key from API:', d.api_key);
          console.log('API Key type:', typeof d.api_key);
          console.log('API Key length:', (d.api_key as string).length);
        }
        
        // 设置默认值
        const parameters = d.parameters as Record<string, number | boolean | string> || {};
        
        form.setFieldsValue({
          base_url: d.base_url,
          api_key: d.api_key,
          model: d.model,
          sample_rate: parameters.sample_rate !== undefined ? parameters.sample_rate : 16000,
          format: parameters.format !== undefined ? parameters.format : 'pcm',
          language: parameters.language !== undefined ? parameters.language : 'zh-CN',
          enable_punctuation: parameters.enable_punctuation !== undefined ? parameters.enable_punctuation : true,
          enable_itn: parameters.enable_itn !== undefined ? parameters.enable_itn : true,
          enable_vad: parameters.enable_vad !== undefined ? parameters.enable_vad : true,
          vad_silence_timeout: parameters.vad_silence_timeout !== undefined ? parameters.vad_silence_timeout : 800,
          max_sentence_length: parameters.max_sentence_length !== undefined ? parameters.max_sentence_length : 100,
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
        console.error('Failed to load STT config:', error);
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      await configApi.updateSTT({
        base_url: values.base_url,
        api_key: values.api_key,
        model: values.model,
        parameters: {
          sample_rate: values.sample_rate,
          format: values.format,
          language: values.language,
          enable_punctuation: values.enable_punctuation,
          enable_itn: values.enable_itn,
          enable_vad: values.enable_vad,
          vad_silence_timeout: values.vad_silence_timeout,
          max_sentence_length: values.max_sentence_length,
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
      const { data } = await configApi.validateSTT({
        base_url: values.base_url,
        api_key: values.api_key,
        model: values.model,
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
      <Card title="STT 配置">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
            <Input placeholder="wss://dashscope.aliyuncs.com/api-ws/v1/inference" />
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
            <Input placeholder="paraformer-realtime-v2" />
          </Form.Item>
          
          <Divider orientation="left">音频参数</Divider>
          
          <Form.Item name="sample_rate" label="Sample Rate">
            <InputNumber min={8000} max={48000} step={8000} defaultValue={16000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="format" label="Format">
            <Input placeholder="pcm" />
          </Form.Item>
          <Form.Item name="language" label="Language">
            <Input placeholder="zh-CN" />
          </Form.Item>
          
          <Divider orientation="left">高级参数</Divider>
          
          <Form.Item name="enable_punctuation" label="启用标点" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          <Form.Item name="enable_itn" label="启用数字转换" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          <Form.Item name="enable_vad" label="启用静音检测" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          <Form.Item name="vad_silence_timeout" label="静音超时（毫秒）">
            <InputNumber min={100} max={3000} step={100} defaultValue={800} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="max_sentence_length" label="最大句子长度">
            <InputNumber min={10} max={500} step={10} defaultValue={100} style={{ width: '100%' }} />
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
