import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { lazy } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { LazyLoad } from './components/LoadingFallback';
import Layout from './pages/Layout';
import Login from './pages/Login';

// 懒加载页面组件
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ConfigLLM = lazy(() => import('./pages/ConfigLLM'));
const ConfigSTT = lazy(() => import('./pages/ConfigSTT'));
const ConfigTTS = lazy(() => import('./pages/ConfigTTS'));
const ConfigSRS = lazy(() => import('./pages/ConfigSRS'));
const Clients = lazy(() => import('./pages/Clients'));
const ClientManagement = lazy(() => import('./pages/ClientManagement'));
const SessionConfig = lazy(() => import('./pages/SessionConfig'));
const Monitor = lazy(() => import('./pages/Monitor'));
const Users = lazy(() => import('./pages/Users'));
const AuditLogs = lazy(() => import('./pages/AuditLogs'));

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
            <Route index element={<LazyLoad><Dashboard /></LazyLoad>} />
            <Route path="config/llm" element={<LazyLoad><ConfigLLM /></LazyLoad>} />
            <Route path="config/stt" element={<LazyLoad><ConfigSTT /></LazyLoad>} />
            <Route path="config/tts" element={<LazyLoad><ConfigTTS /></LazyLoad>} />
            <Route path="config/srs" element={<LazyLoad><ConfigSRS /></LazyLoad>} />
            <Route path="clients" element={<LazyLoad><Clients /></LazyLoad>} />
            <Route path="session-config" element={<LazyLoad><SessionConfig /></LazyLoad>} />
            <Route path="monitor" element={<LazyLoad><Monitor /></LazyLoad>} />
            <Route path="users" element={<LazyLoad><Users /></LazyLoad>} />
            <Route path="client-management" element={<LazyLoad><ClientManagement /></LazyLoad>} />
            <Route path="audit-logs" element={<LazyLoad><AuditLogs /></LazyLoad>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}