import { Button, Card, Divider, Form, Input, InputNumber, message, Space, Switch, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigTTS() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string>(''); // 测试结果状态
  const [showApiKey, setShowApiKey] = useState(true); // 默认显示明文密钥
  
  useEffect(() => {
    console.log('ConfigTTS component mounted, loading config...');
    const loadConfig = async () => {
      try {
        console.log('Calling configApi.getTTS()...');
        const r = await configApi.getTTS();
        console.log('API response received:', r);
        const d = r.data.data as unknown as Record<string, unknown> || {};
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
          voice: parameters.voice !== undefined ? parameters.voice : 'zhimiao',
          speech_rate: parameters.speech_rate !== undefined ? parameters.speech_rate : 0,
          pitch: parameters.pitch !== undefined ? parameters.pitch : 0,
          volume: parameters.volume !== undefined ? parameters.volume : 0,
          format: parameters.format !== undefined ? parameters.format : 'pcm',
          sample_rate: parameters.sample_rate !== undefined ? parameters.sample_rate : 24000,
          enable_subtitle: parameters.enable_subtitle !== undefined ? parameters.enable_subtitle : false,
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
        console.error('Failed to load TTS config:', error);
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      await configApi.updateTTS({
        base_url: values.base_url as string,
        api_key: values.api_key as string,
        model: values.model as string,
        parameters: {
          voice: values.voice as string,
          speech_rate: values.speech_rate as number,
          pitch: values.pitch as number,
          volume: values.volume as number,
          format: values.format as string,
          sample_rate: values.sample_rate as number,
          enable_subtitle: values.enable_subtitle as boolean,
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
      const { data } = await configApi.validateTTS({
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
      <Card title="TTS 配置">
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
            <Input placeholder="cosyvoice-v3-plus" />
          </Form.Item>
          
          <Divider orientation="left">语音参数</Divider>
          
          <Form.Item name="voice" label="Voice">
            <Input placeholder="zhimiao" />
          </Form.Item>
          <Form.Item name="speech_rate" label="Speech Rate">
            <InputNumber min={-500} max={500} step={50} defaultValue={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="pitch" label="Pitch">
            <InputNumber min={-500} max={500} step={50} defaultValue={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="volume" label="Volume">
            <InputNumber min={-500} max={500} step={50} defaultValue={0} style={{ width: '100%' }} />
          </Form.Item>
          
          <Divider orientation="left">音频参数</Divider>
          
          <Form.Item name="format" label="Format">
            <Input placeholder="pcm" />
          </Form.Item>
          <Form.Item name="sample_rate" label="Sample Rate">
            <InputNumber min={8000} max={48000} step={8000} defaultValue={24000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="enable_subtitle" label="启用字幕" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
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
