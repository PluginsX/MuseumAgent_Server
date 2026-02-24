import { useEffect, useState } from 'react';
import { Card, Form, Input, Button, message, Space, InputNumber, Typography } from 'antd';
import axios from 'axios';

interface MySQLConfig {
  mysql_host: string;
  mysql_port: number;
  mysql_user: string;
  mysql_password: string;
  mysql_db: string;
  mysql_charset: string;
  mysql_pool_size: number;
  mysql_pool_recycle: number;
}

export default function ConfigMySQL() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'unknown' | 'success' | 'error'>('unknown');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/admin/config/mysql/raw', {
        headers: { Authorization: `Bearer ${token}` }
      });
      form.setFieldsValue(response.data);
    } catch (error: any) {
      message.error('加载MySQL配置失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const onFinish = async (values: MySQLConfig) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      await axios.put('/api/admin/config/mysql', values, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('MySQL配置保存成功');
      message.warning('修改数据库配置后需要重启服务才能生效');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    const values = form.getFieldsValue();
    
    if (!values.mysql_host || !values.mysql_user || !values.mysql_db) {
      message.warning('请先填写MySQL主机、用户名和数据库名');
      setTestResult('error');
      return;
    }

    try {
      setTesting(true);
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/admin/config/mysql/validate', {
        mysql_host: values.mysql_host,
        mysql_port: values.mysql_port,
        mysql_user: values.mysql_user,
        mysql_password: values.mysql_password,
        mysql_db: values.mysql_db
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.valid) {
        message.success(response.data.message);
        setTestResult('success');
      } else {
        message.error(response.data.message);
        setTestResult('error');
      }
    } catch (error: any) {
      message.error('连接测试失败');
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="MySQL 数据库配置" loading={loading}>
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={onFinish}
          initialValues={{
            mysql_host: '127.0.0.1',
            mysql_port: 3306,
            mysql_user: 'root',
            mysql_password: '',
            mysql_db: 'museum_artifact',
            mysql_charset: 'utf8mb4',
            mysql_pool_size: 10,
            mysql_pool_recycle: 3600
          }}
        >
          <Form.Item 
            name="mysql_host" 
            label="主机地址" 
            rules={[{ required: true, message: '请输入MySQL主机地址' }]}
          >
            <Input placeholder="例如: 127.0.0.1 或 localhost" />
          </Form.Item>
          
          <Form.Item 
            name="mysql_port" 
            label="端口" 
            rules={[{ required: true, message: '请输入MySQL端口' }]}
          >
            <InputNumber 
              min={1} 
              max={65535} 
              placeholder="默认: 3306" 
              style={{ width: '100%' }} 
            />
          </Form.Item>
          
          <Form.Item 
            name="mysql_user" 
            label="用户名" 
            rules={[{ required: true, message: '请输入MySQL用户名' }]}
          >
            <Input placeholder="例如: root" />
          </Form.Item>
          
          <Form.Item 
            name="mysql_password" 
            label="密码" 
            rules={[{ required: true, message: '请输入MySQL密码' }]}
          >
            <Input placeholder="请输入MySQL密码" />
          </Form.Item>
          
          <Form.Item 
            name="mysql_db" 
            label="数据库名" 
            rules={[{ required: true, message: '请输入数据库名' }]}
          >
            <Input placeholder="例如: museum_artifact" />
          </Form.Item>
          
          <Form.Item name="mysql_charset" label="字符集">
            <Input placeholder="默认: utf8mb4" />
          </Form.Item>
          
          <Form.Item 
            name="mysql_pool_size" 
            label="连接池大小"
            tooltip="数据库连接池的最大连接数"
          >
            <InputNumber 
              min={1} 
              max={100} 
              placeholder="默认: 10" 
              style={{ width: '100%' }} 
            />
          </Form.Item>
          
          <Form.Item 
            name="mysql_pool_recycle" 
            label="连接回收时间（秒）"
            tooltip="连接在连接池中的最大存活时间"
          >
            <InputNumber 
              min={60} 
              max={86400} 
              placeholder="默认: 3600" 
              style={{ width: '100%' }} 
            />
          </Form.Item>
          
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存配置
              </Button>
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


