import { AreaChartOutlined, BookOutlined, ClockCircleOutlined, CodeOutlined, DesktopOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, SettingOutlined, TeamOutlined } from '@ant-design/icons';
import { Layout as AntLayout, Button, Menu, Space, Typography } from 'antd';
import { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/', label: <Link to="/">仪表盘</Link>, icon: <SettingOutlined /> },
  { key: '/config/llm', label: <Link to="/config/llm">LLM 配置</Link>, icon: <CodeOutlined /> },
  { key: '/config/stt', label: <Link to="/config/stt">STT 配置</Link>, icon: <CodeOutlined /> },
  { key: '/config/tts', label: <Link to="/config/tts">TTS 配置</Link>, icon: <CodeOutlined /> },
  { key: '/config/srs', label: <Link to="/config/srs">SRS配置</Link>, icon: <BookOutlined /> },
  { key: '/clients', label: <Link to="/clients">客户信息</Link>, icon: <DesktopOutlined /> },
  { key: '/session-config', label: <Link to="/session-config">会话配置</Link>, icon: <ClockCircleOutlined /> },
  { key: '/monitor', label: <Link to="/monitor">系统监控</Link>, icon: <AreaChartOutlined /> },
  { key: '/users', label: <Link to="/users">用户管理</Link>, icon: <TeamOutlined /> },
  { key: '/client-management', label: <Link to="/client-management">客户管理</Link>, icon: <TeamOutlined /> },
  { key: '/audit-logs', label: <Link to="/audit-logs">审计日志</Link>, icon: <BookOutlined /> },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem('token');
    navigate('/login', { replace: true });
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        style={{
          background: '#304156',
          boxShadow: '2px 0 8px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#ffffff',
          fontSize: '18px',
          fontWeight: 600,
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'linear-gradient(135deg, #304156 0%, #263445 100%)',
        }}>
          {collapsed ? 'M' : 'MuseumAgent'}
        </div>
        <Menu 
          theme="dark" 
          mode="inline" 
          defaultSelectedKeys={['/']} 
          items={menuItems}
          style={{
            background: 'transparent',
            borderRight: 'none',
          }}
        />
      </Sider>
      <AntLayout>
        <Header style={{ 
          padding: '0 24px', 
          background: '#ffffff',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
          zIndex: 10,
        }}>
          <Button 
            type="text" 
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} 
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              color: '#303133',
              transition: 'all 0.3s',
            }}
          />
          <Space>
            <Typography.Text style={{ color: '#909399', fontSize: '14px' }}>
              控制面板
            </Typography.Text>
            <Button 
              type="text" 
              icon={<LogoutOutlined />} 
              onClick={logout}
              style={{
                color: '#f56c6c',
                transition: 'all 0.3s',
              }}
            >
              退出
            </Button>
          </Space>
        </Header>
        <Content style={{ 
          margin: '24px', 
          padding: 24, 
          background: '#ffffff',
          borderRadius: 4,
          boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)',
          minHeight: 'calc(100vh - 112px)',
        }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
