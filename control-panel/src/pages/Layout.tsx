import { LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, SettingOutlined } from '@ant-design/icons';
import { Button, Layout as AntLayout, Menu, Space, Typography } from 'antd';
import { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/', label: <Link to="/">仪表盘</Link>, icon: <SettingOutlined /> },
  { key: '/config/llm', label: <Link to="/config/llm">LLM 配置</Link> },
  { key: '/config/embedding', label: <Link to="/config/embedding">Embedding 配置</Link> },
  { key: '/embedding', label: <Link to="/embedding">向量化</Link> },
  { key: '/monitor', label: <Link to="/monitor">系统监控</Link> },
  { key: '/users', label: <Link to="/users">用户管理</Link> },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem('token');
    navigate('/Control/login');
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
          {collapsed ? 'M' : 'MuseumAgent'}
        </div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['/']} items={menuItems} />
      </Sider>
      <AntLayout>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} />
          <Space>
            <Typography.Text type="secondary">控制面板</Typography.Text>
            <Button type="text" icon={<LogoutOutlined />} onClick={logout}>退出</Button>
          </Space>
        </Header>
        <Content style={{ margin: '24px', padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
