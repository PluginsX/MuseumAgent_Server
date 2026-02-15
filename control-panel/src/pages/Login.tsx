import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, message } from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../api/client';
import { extractData, getErrorMessage } from '../utils/helpers';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response = await auth.login(values.username, values.password);
      const data = extractData<{ access_token: string }>(response);
      
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        message.success('登录成功');
        navigate('/', { replace: true });
      } else {
        message.error('登录失败：未获取到认证令牌');
      }
    } catch (error) {
      message.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card 
        title={
          <div style={{ textAlign: 'center', fontSize: '20px', fontWeight: 600 }}>
            MuseumAgent 控制面板
          </div>
        }
        style={{ 
          width: 400, 
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
          borderRadius: 8
        }}
      >
        <Form name="login" onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item 
            name="username" 
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
            />
          </Form.Item>
          <Form.Item 
            name="password" 
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码" 
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
