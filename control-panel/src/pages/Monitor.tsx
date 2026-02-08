import { Button, Card, Descriptions, Space, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import { monitorApi } from '../api/client';

export default function Monitor() {
  const [status, setStatus] = useState<Record<string, unknown>>({});
  const [logs, setLogs] = useState<{ lines: string[]; total: number }>({ lines: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false); // 清空日志的加载状态

  useEffect(() => {
    console.log('Monitor component mounted');
    loadStatus();
    loadLogs();
  }, []);

  const loadStatus = async () => {
    try {
      console.log('Loading status...');
      const response = await monitorApi.status();
      console.log('Status response:', response);
      setStatus(response.data.data);
      message.success('状态加载成功');
    } catch (error: any) {
      console.error('Status load error:', error);
      message.error(`状态加载失败: ${error.response?.data?.msg || error.message}`);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      console.log('Loading logs...');
      const response = await monitorApi.logs({ page: 1, size: 50 });
      console.log('Logs response:', response);
      setLogs(response.data.data);
      message.success('日志加载成功');
    } catch (error: any) {
      console.error('Logs load error:', error);
      message.error(`日志加载失败: ${error.response?.data?.msg || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    setClearing(true);
    try {
      console.log('Clearing logs...');
      await monitorApi.clearLogs();
      setLogs({ lines: [], total: 0 });
      message.success('日志已清空');
      loadLogs();
    } catch (error: any) {
      console.error('Clear logs error:', error);
      message.error(`清空日志失败: ${error.response?.data?.msg || error.message}`);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography.Title level={5}>系统状态</Typography.Title>
      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="服务状态">{String(status.service_status ?? '-')}</Descriptions.Item>
          <Descriptions.Item label="版本">{String(status.version ?? '-')}</Descriptions.Item>
          <Descriptions.Item label="运行时间">{String(status.uptime ?? '-')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Typography.Title level={5}>
        最近日志
        <Space style={{ marginLeft: 16 }}>
          <Button size="small" onClick={loadLogs} loading={loading}>
            刷新
          </Button>
          <Button size="small" danger onClick={clearLogs} loading={clearing}>
            清空日志
          </Button>
        </Space>
      </Typography.Title>
      <Card style={{ flex: 1, minHeight: 200, display: 'flex', flexDirection: 'column' }}>
        <pre style={{ flex: 1, overflow: 'auto', fontSize: 12, margin: 0, padding: '16px' }}>
          {logs.lines?.length ? logs.lines.join('\n') : '暂无日志'}
        </pre>
      </Card>
    </div>
  );
}