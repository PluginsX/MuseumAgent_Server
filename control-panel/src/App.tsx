import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import ConfigEmbedding from './pages/ConfigEmbedding';
import ConfigLLM from './pages/ConfigLLM';
import Dashboard from './pages/Dashboard';
import EmbeddingPage from './pages/EmbeddingPage';
import Layout from './pages/Layout';
import Login from './pages/Login';
import Monitor from './pages/Monitor';
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
        colorPrimary: '#808080',
        colorBgBase: '#000000',
        colorTextBase: '#ffffff',
        colorBorder: '#333333',
        colorFill: '#1a1a1a',
        colorFillSecondary: '#2a2a2a',
      },
      algorithm: theme.darkAlgorithm, // 暗黑主题算法
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
            <Route path="config/embedding" element={<ConfigEmbedding />} />
            <Route path="embedding" element={<EmbeddingPage />} />
            <Route path="monitor" element={<Monitor />} />
            <Route path="users" element={<Users />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}