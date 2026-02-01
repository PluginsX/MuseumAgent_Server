import { Button, Card, Descriptions, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { monitorApi } from '../api/client';

export default function Monitor() {
  const [status, setStatus] = useState<Record<string, unknown>>({});
  const [logs, setLogs] = useState<{ lines: string[]; total: number }>({ lines: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false); // 清空日志的加载状态

  useEffect(() => {
    monitorApi.status().then((r) => setStatus(r.data)).catch(() => {});
    loadLogs();
  }, []);

  const loadLogs = () => {
    setLoading(true);
    monitorApi.logs({ page: 1, size: 50 })
      .then((r) => setLogs(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const clearLogs = async () => {
    setClearing(true);
    try {
      await monitorApi.clearLogs(); // 调用后端API清空日志
      setLogs({ lines: [], total: 0 }); // 清空本地显示
      loadLogs(); // 重新加载日志（此时应该为空）
    } catch (e: unknown) {
      console.error('清空日志失败:', e);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div>
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
      <Card>
        <pre style={{ maxHeight: 400, overflow: 'auto', fontSize: 12 }}>
          {logs.lines?.length ? logs.lines.join('\n') : '暂无日志'}
        </pre>
      </Card>
    </div>
  );
}