import { ClockCircleOutlined, DesktopOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, SettingOutlined, TeamOutlined } from '@ant-design/icons';
import { Layout as AntLayout, Button, Menu, Space, Typography } from 'antd';
import { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/', label: <Link to="/">仪表盘</Link>, icon: <SettingOutlined /> },
  { key: '/config/llm', label: <Link to="/config/llm">LLM 配置</Link> },
  { key: '/config/embedding', label: <Link to="/config/embedding">Embedding 配置</Link> },
  { key: '/embedding', label: <Link to="/embedding">向量化</Link> },
  { key: '/clients', label: <Link to="/clients">客户端信息</Link>, icon: <DesktopOutlined /> },
  { key: '/session-config', label: <Link to="/session-config">会话配置</Link>, icon: <ClockCircleOutlined /> },
  { key: '/monitor', label: <Link to="/monitor">系统监控</Link> },
  { key: '/users', label: <Link to="/users">用户管理</Link>, icon: <TeamOutlined /> },
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
        <Header style={{ padding: '0 16px', background: '#1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} />
          <Space>
            <Typography.Text type="secondary">控制面板</Typography.Text>
            <Button type="text" icon={<LogoutOutlined />} onClick={logout}>退出</Button>
          </Space>
        </Header>
        <Content style={{ margin: '24px', padding: 24, background: '#1a1a1a', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
