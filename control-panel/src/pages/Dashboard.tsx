import { Button, Card, Form, Input, message, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { configApi } from '../api/client';

export default function Dashboard() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [initialConfig, setInitialConfig] = useState<string>('');

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
        console.log('Loading server config...');
        console.log('Calling configApi.getServer()...');
        const response = await configApi.getServer();
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
        console.error('Failed to load server config:', error);
        message.error('加载配置失败');
      }
    };
    
    loadConfig();
  }, [form]);
  
  const onFinish = async (values: { config: string }) => {
    setLoading(true);
    try {
      console.log('Saving server config:', values);
      
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
      
      await configApi.updateServer(configData as any);
      message.success('保存成功，请重启服务器以应用配置！');
      alert('保存成功，请重启服务器以应用配置！');
      
      // 保存成功后重置初始配置和未保存修改状态
      setInitialConfig(values.config);
      setHasUnsavedChanges(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail || '保存失败');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <Card title="服务器配置">
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
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}