import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Tag, Typography, Input, Modal, Descriptions, Badge, Statistic, Row, Col, message } from 'antd';
import { ReloadOutlined, SearchOutlined, DisconnectOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { api } from '../api/client';

const { Title, Text } = Typography;
const { Search } = Input;

interface ClientInfo {
  session_id: string;
  client_type: string;
  client_id: string;
  platform: string;
  client_version: string;
  ip_address: string;
  created_at: string;
  expires_at: string;
  is_active: boolean;
  function_names: string[];
  function_count: number;
  last_heartbeat: string;
  time_since_heartbeat: number;
}

interface ClientStats {
  total_clients: number;
  active_sessions: number;
  inactive_sessions: number;
  client_types: Record<string, number>;
  timestamp: string;
}

export default function Clients() {
  const [clients, setClients] = useState<ClientInfo[]>([]);
  const [filteredClients, setFilteredClients] = useState<ClientInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<ClientStats | null>(null);
  const [selectedClient, setSelectedClient] = useState<ClientInfo | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // 获取客户端列表
  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/admin/clients/connected');
      setClients(response.data);
      setFilteredClients(response.data);
    } catch (error: any) {
      message.error('获取客户端信息失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 获取统计信息
  const fetchStats = async () => {
    try {
      const response = await api.get('/api/admin/clients/stats');
      setStats(response.data);
    } catch (error: any) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 断开客户端连接
  const disconnectClient = async (session_id: string) => {
    Modal.confirm({
      title: '确认断开连接',
      content: '确定要断开此客户端的连接吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/api/admin/clients/session/${session_id}`);
          message.success('客户端连接已断开');
          fetchClients();
          fetchStats();
        } catch (error: any) {
          message.error('断开连接失败: ' + (error.response?.data?.detail || error.message));
        }
      }
    });
  };

  // 查看客户端详情
  const showClientDetails = async (client: ClientInfo) => {
    setSelectedClient(client);
    setDetailModalVisible(true);
  };

  // 搜索过滤
  const handleSearch = (value: string) => {
    if (!value.trim()) {
      setFilteredClients(clients);
      return;
    }
    
    const filtered = clients.filter(client => 
      client.client_type.toLowerCase().includes(value.toLowerCase()) ||
      client.client_id.toLowerCase().includes(value.toLowerCase()) ||
      client.platform.toLowerCase().includes(value.toLowerCase()) ||
      client.ip_address.includes(value) ||
      client.session_id.includes(value)
    );
    setFilteredClients(filtered);
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchClients();
    fetchStats();
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchClients();
    fetchStats();
    
    // 设置定时刷新（每10秒）
    const interval = setInterval(() => {
      fetchClients();
      fetchStats();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '序号',
      key: 'index',
      render: (_: any, __: any, index: number) => index + 1,
      width: 60,
    },
    {
      title: '客户端类型',
      dataIndex: 'client_type',
      key: 'client_type',
      render: (type: string) => (
        <Tag color={type === 'spirit' ? 'blue' : type === 'web' ? 'green' : 'default'}>
          {type || 'unknown'}
        </Tag>
      ),
      sorter: (a: ClientInfo, b: ClientInfo) => (a.client_type || '').localeCompare(b.client_type || ''),
    },
    {
      title: '客户端ID',
      dataIndex: 'client_id',
      key: 'client_id',
      ellipsis: true,
      render: (id: string) => <Text copyable={{ tooltips: ['复制', '已复制'] }}>{id}</Text>,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip: string) => <Text code>{ip}</Text>,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (platform: string) => <Tag>{platform || 'unknown'}</Tag>,
    },
    {
      title: '版本',
      dataIndex: 'client_version',
      key: 'client_version',
      render: (version: string) => version || '-',
    },
    {
      title: '会话ID',
      dataIndex: 'session_id',
      key: 'session_id',
      ellipsis: true,
      render: (id: string) => <Text copyable={{ tooltips: ['复制', '已复制'] }}>{id.substring(0, 8)}...</Text>,
    },
    {
      title: '指令集数量',
      dataIndex: 'function_count',
      key: 'function_count',
      render: (count: number) => <Badge count={count} showZero color="#1890ff" />,
      sorter: (a: ClientInfo, b: ClientInfo) => a.function_count - b.function_count,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Badge status={active ? 'success' : 'error'} text={active ? '活跃' : '非活跃'} />
      ),
      sorter: (a: ClientInfo, b: ClientInfo) => Number(a.is_active) - Number(b.is_active),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ClientInfo) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<InfoCircleOutlined />}
            onClick={() => showClientDetails(record)}
          >
            详情
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger 
            icon={<DisconnectOutlined />}
            onClick={() => disconnectClient(record.session_id)}
          >
            断开
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>客户端信息管理</Title>
      
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="总客户端数" 
                value={stats.total_clients} 
                suffix="个"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="活跃会话" 
                value={stats.active_sessions} 
                suffix="个"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="非活跃会话" 
                value={stats.inactive_sessions} 
                suffix="个"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="客户端类型" 
                value={Object.keys(stats.client_types).length} 
                suffix="种"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 搜索和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search
            placeholder="搜索客户端类型、ID、IP地址或会话ID"
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            onSearch={handleSearch}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 300 }}
          />
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
          <Text type="secondary">
            实时更新间隔: 10秒 (服务端自动检测僵尸会话)
          </Text>
        </Space>
      </Card>

      {/* 客户端列表表格 - 自动填满剩余空间 */}
      <Card style={{ flex: 1, overflow: 'hidden' }}>
        <Table
          dataSource={filteredClients}
          columns={columns}
          rowKey="session_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ y: 'calc(100vh - 380px)', x: 1200 }}
          style={{ height: '100%' }}
        />
      </Card>

      {/* 客户端详情模态框 */}
      <Modal
        title="客户端详细信息"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={
          <Space>
            <Button key="close" onClick={() => setDetailModalVisible(false)}>
              关闭
            </Button>
            {selectedClient && (
              <Button 
                key="disconnect" 
                danger 
                icon={<DisconnectOutlined />}
                onClick={() => {
                  disconnectClient(selectedClient.session_id);
                  // 不要立即关闭模态框，等待用户确认后再关闭
                }}
              >
                断开连接
              </Button>
            )}
          </Space>
        }
        width={800}
      >
        {selectedClient && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="会话ID" span={2}>
              <Text copyable>{selectedClient.session_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="客户端类型">
              <Tag color={selectedClient.client_type === 'spirit' ? 'blue' : 'default'}>
                {selectedClient.client_type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="客户端ID">
              <Text copyable>{selectedClient.client_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="平台">{selectedClient.platform}</Descriptions.Item>
            <Descriptions.Item label="版本">{selectedClient.client_version}</Descriptions.Item>
            <Descriptions.Item label="IP地址">
              <Text code>{selectedClient.ip_address}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Badge 
                status={selectedClient.is_active ? 'success' : 'error'} 
                text={selectedClient.is_active ? '活跃' : '非活跃'} 
              />
            </Descriptions.Item>
            <Descriptions.Item label="距离上次心跳">
              {Math.floor(selectedClient.time_since_heartbeat / 60)} 分钟
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedClient.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="过期时间">
              {new Date(selectedClient.expires_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="指令集" span={2}>
              <Space wrap>
                {selectedClient.function_names.map((op, index) => (
                  <Tag key={index} color="processing">{op}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}