import { Button, Card, Form, Input, message, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function ConfigLLM() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [initialConfig, setInitialConfig] = useState<string>('');
  const [testResult, setTestResult] = useState<'unknown' | 'success' | 'error'>('unknown');

  // 监听配置修改
  const handleConfigChange = (value: string) => {
    if (initialConfig && value !== initialConfig) {
      setHasUnsavedChanges(true);
    } else {
      setHasUnsavedChanges(false);
    }
  };
  
  useEffect(() => {
    const loadConfig = async () => {
      try {
        console.log('Loading LLM config...');
        console.log('Calling configApi.getLLM()...');
        const response = await configApi.getLLM();
        console.log('API response received:', response);
        
        // 尝试从不同的位置获取配置数据
        let data: Record<string, unknown> = {};
        
        // 检查response是否是一个对象
        if (typeof response === 'object' && response !== null) {
          // 检查是否有data字段（axios响应格式）
          if ('data' in response && typeof response.data === 'object' && response.data !== null) {
            const responseData = response.data as any;
            console.log('Response data:', responseData);
            
            // 直接使用responseData作为配置数据
            data = { ...responseData };
            console.log('Config data from response.data:', data);
          } else {
            console.log('No data field found in response');
          }
        } else {
          console.error('Invalid API response format:', response);
        }
        
        // 将配置数据转换为JSON字符串，用于显示在文本框中
        const jsonString = JSON.stringify(data, null, 2);
        form.setFieldsValue({ config: jsonString });
        setInitialConfig(jsonString); // 保存初始配置
        setHasUnsavedChanges(false); // 重置未保存修改状态
        console.log('Form values set:', jsonString);
      } catch (error) {
        console.error('Failed to load LLM config:', error);
        message.error('加载配置失败');
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: { config: string }) => {
    setLoading(true);
    try {
      console.log('Saving LLM config:', values);
      
      // 解析JSON字符串为对象
      let configData: Record<string, unknown> = {};
      try {
        configData = JSON.parse(values.config);
        console.log('Parsed config data:', configData);
      } catch (parseError) {
        console.error('Failed to parse JSON:', parseError);
        message.error('JSON格式错误，请检查配置内容');
        alert('JSON格式错误，请检查配置内容');
        return;
      }
      
      await configApi.updateLLM(configData as any);
      message.success('保存成功');
      alert('保存成功');
      
      // 保存成功后重置初始配置和未保存修改状态
      setInitialConfig(values.config);
      setHasUnsavedChanges(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      const errorMessage = err.response?.data?.detail || '保存失败';
      message.error(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  const testConnection = async () => {
    const values = form.getFieldsValue();
    if (!values.config) {
      message.warning('请先填写配置内容');
      return;
    }
    
    try {
      // 解析JSON字符串为对象
      const configData = JSON.parse(values.config);
      if (!configData.base_url || !configData.api_key || !configData.model) {
        message.warning('请先填写 Base URL、API Key 和 Model');
        return;
      }
      
      setTesting(true);
      console.log('Testing LLM connection...');
      
      // 异步执行测试连接，不阻塞主线程
      const response = await configApi.validateLLM({
        base_url: configData.base_url as string,
        api_key: configData.api_key as string,
        model: configData.model as string,
      });
      
      console.log('LLM validation response:', response);
      
      // 处理响应数据，使用类型断言绕过TypeScript类型检查
      let isValid = false;
      let messageText = '连接失败';
      
      try {
        // 检查直接响应对象
        const responseAny = response as any;
        if (responseAny.valid !== undefined) {
          isValid = responseAny.valid;
          messageText = responseAny.message || (isValid ? '连接成功' : '连接失败');
        } 
        // 检查response.data
        else if (responseAny.data && responseAny.data.valid !== undefined) {
          isValid = responseAny.data.valid;
          messageText = responseAny.data.message || (isValid ? '连接成功' : '连接失败');
        } 
        // 检查response.data.data
        else if (responseAny.data && responseAny.data.data && responseAny.data.data.valid !== undefined) {
          isValid = responseAny.data.data.valid;
          messageText = responseAny.data.data.message || (isValid ? '连接成功' : '连接失败');
        }
      } catch (e) {
        console.error('Error processing validation response:', e);
      }
      
      console.log('LLM validation result:', { isValid, messageText });
      
      if (isValid) {
        message.success(messageText);
        setTestResult('success');
      } else {
        message.error(messageText);
        setTestResult('error');
      }
    } catch (e: unknown) {
      if (e instanceof SyntaxError) {
        console.error('Failed to parse JSON:', e);
        message.error('JSON格式错误，请检查配置内容');
        setTestResult('error');
      } else {
        console.error('LLM validation error:', e);
        const err = e as { response?: { data?: { message?: string } } };
        const errorMsg = err.response?.data?.message || '连接失败';
        message.error(errorMsg);
        setTestResult('error');
      }
    } finally {
      setTesting(false);
    }
  };
  
  return (
    <div>
      <Card title="LLM 配置">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="config" label="配置内容（JSON格式）">
            <Input.TextArea 
              rows={15} 
              placeholder="请输入JSON格式的配置内容"
              spellCheck={false}
              style={{ fontFamily: 'monospace' }}
              onChange={(e) => handleConfigChange(e.target.value)}
            />
          </Form.Item>
          
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Space style={{ flex: 1, justifyContent: 'space-between' }}>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存配置
                </Button>
                {hasUnsavedChanges && (
                  <Typography.Text type="warning" style={{ marginLeft: 8 }}>
                    有未保存的修改
                  </Typography.Text>
                )}
              </Space>
              <Space>
                {testing ? (
                  <Typography.Text style={{ marginRight: 8 }}>测试中...</Typography.Text>
                ) : testResult === 'success' ? (
                  <Typography.Text type="success" style={{ marginRight: 8 }}>连接正常</Typography.Text>
                ) : testResult === 'error' ? (
                  <Typography.Text type="danger" style={{ marginRight: 8 }}>连接失败</Typography.Text>
                ) : null}
                <Button onClick={testConnection} loading={testing}>
                  测试连接
                </Button>
              </Space>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}