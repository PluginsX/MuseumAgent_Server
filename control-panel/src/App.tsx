import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Clients from './pages/Clients';
import ConfigLLM from './pages/ConfigLLM';
import ConfigSRS from './pages/ConfigSRS';
import Dashboard from './pages/Dashboard';
import Layout from './pages/Layout';
import Login from './pages/Login';
import Monitor from './pages/Monitor';
import SessionConfig from './pages/SessionConfig';
import Users from './pages/Users';

function Protected({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{
      token: {
        colorPrimary: '#42b883',
        colorSuccess: '#42b883',
        colorWarning: '#f7ba2a',
        colorError: '#f56c6c',
        colorInfo: '#909399',
        colorBgBase: '#ffffff',
        colorTextBase: '#303133',
        colorBorder: '#dcdfe6',
        colorFill: '#f5f7fa',
        colorFillSecondary: '#e4e7ed',
        borderRadius: 4,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      },
      components: {
        Layout: {
          headerBg: '#ffffff',
          siderBg: '#304156',
          bodyBg: '#f0f2f5',
        },
        Menu: {
          darkItemBg: '#304156',
          darkItemSelectedBg: '#42b883',
          darkItemHoverBg: '#263445',
          darkItemColor: '#bfcbd9',
          darkItemSelectedColor: '#ffffff',
        },
        Card: {
          colorBgContainer: '#ffffff',
          colorBorderSecondary: '#e4e7ed',
        },
        Button: {
          colorPrimary: '#42b883',
          colorPrimaryHover: '#66c2a4',
          colorPrimaryActive: '#33a069',
          borderRadius: 4,
        },
        Input: {
          colorBgContainer: '#ffffff',
          colorBorder: '#dcdfe6',
          borderRadius: 4,
        },
        Table: {
          headerBg: '#f5f7fa',
          headerColor: '#909399',
          borderColor: '#ebeef5',
        },
        Form: {
          itemMarginBottom: 24,
          verticalLabelPadding: '0 0 8px',
        },
      },
    }}>
      <BrowserRouter basename="/Control">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <Protected>
                <Layout />
              </Protected>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="config/llm" element={<ConfigLLM />} />
            <Route path="config/srs" element={<ConfigSRS />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/session-config" element={<SessionConfig />} />
            <Route path="monitor" element={<Monitor />} />
            <Route path="users" element={<Users />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}