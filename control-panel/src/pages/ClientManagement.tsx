import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Tag, Typography, Input, Modal, Badge, message, Form, Select } from 'antd';
import { UserAddOutlined, DeleteOutlined, KeyOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { clientsApiExtended } from '../api/client';
import { extractData, formatDateTime, getErrorMessage } from '../utils/helpers';
import type { User } from '../types';

const { Title } = Typography;
const { Search } = Input;

export default function ClientManagement() {
  const [clients, setClients] = useState<User[]>([]);
  const [filteredClients, setFilteredClients] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [resetKeyModalVisible, setResetKeyModalVisible] = useState(false);
  const [selectedClient, setSelectedClient] = useState<User | null>(null);
  const [newApiKey, setNewApiKey] = useState<string>('');
  const [form] = Form.useForm();

  // 获取客户账户列表
  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await clientsApiExtended.listClients();
      const data = extractData<User[]>(response);
      setClients(data);
      setFilteredClients(data);
    } catch (error) {
      message.error('获取客户账户信息失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // 创建客户账户
  const handleCreateClient = async (values: any) => {
    try {
      const response = await clientsApiExtended.createClient(values);
      const data = extractData<{ api_key: string; user: User }>(response);
      
      setNewApiKey(data.api_key);
      message.success('客户账户创建成功！');
      
      // 显示API密钥
      Modal.success({
        title: '客户创建成功',
        content: (
          <div>
            <p>用户名: {values.username}</p>
            <p>API密钥: <strong>{data.api_key}</strong></p>
            <p style={{ color: '#f56c6c' }}>请妥善保管API密钥，此密钥只显示一次！</p>
          </div>
        ),
        width: 600,
      });
      
      setCreateModalVisible(false);
      form.resetFields();
      fetchClients();
    } catch (error) {
      message.error('创建客户账户失败: ' + getErrorMessage(error));
    }
  };

  // 删除客户账户
  const handleDeleteClient = async (clientId: number) => {
    Modal.confirm({
      title: '确认删除客户',
      content: '确定要删除此客户账户吗？此操作将禁用该客户的访问权限。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await clientsApiExtended.deleteClient(clientId);
          message.success('客户账户删除成功！');
          fetchClients();
        } catch (error) {
          message.error('删除客户账户失败: ' + getErrorMessage(error));
        }
      }
    });
  };

  // 重置API密钥
  const handleResetApiKey = async () => {
    if (!selectedClient) return;

    try {
      const response = await clientsApiExtended.resetApiKey(selectedClient.id);
      const data = extractData<{ api_key: string }>(response);
      
      Modal.success({
        title: 'API密钥重置成功',
        content: (
          <div>
            <p>新的API密钥: <strong>{data.api_key}</strong></p>
            <p style={{ color: '#f56c6c' }}>请妥善保管API密钥，此密钥只显示一次！</p>
          </div>
        ),
        width: 600,
      });
      
      setResetKeyModalVisible(false);
      setSelectedClient(null);
    } catch (error) {
      message.error('重置API密钥失败: ' + getErrorMessage(error));
    }
  };

  // 搜索过滤
  const handleSearch = (value: string) => {
    if (!value.trim()) {
      setFilteredClients(clients);
      return;
    }
    
    const filtered = clients.filter(client => 
      client.username.toLowerCase().includes(value.toLowerCase()) ||
      (client.email && client.email.toLowerCase().includes(value.toLowerCase()))
    );
    setFilteredClients(filtered);
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchClients();
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchClients();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a: User, b: User) => a.id - b.id,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      ellipsis: true,
      sorter: (a: User, b: User) => a.username.localeCompare(b.username),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email?: string) => email || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {role}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Badge status={active ? 'success' : 'error'} text={active ? '激活' : '禁用'} />
      ),
      sorter: (a: User, b: User) => Number(a.is_active) - Number(b.is_active),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatDateTime(date),
      sorter: (a: User, b: User) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date?: string) => date ? formatDateTime(date) : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<KeyOutlined />}
            onClick={() => {
              setSelectedClient(record);
              setResetKeyModalVisible(true);
            }}
          >
            重置密钥
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteClient(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>客户账户管理</Title>
      
      {/* 搜索和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search
            placeholder="搜索用户名或邮箱"
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            onSearch={handleSearch}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 300 }}
          />
          <Button 
            type="primary" 
            icon={<UserAddOutlined />} 
            onClick={() => setCreateModalVisible(true)}
          >
            创建客户
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 客户列表表格 */}
      <Card style={{ flex: 1, overflow: 'hidden' }}>
        <Table
          dataSource={filteredClients}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ y: 'calc(100vh - 300px)', x: 1000 }}
        />
      </Card>

      {/* 创建客户模态框 */}
      <Modal
        title="创建客户账户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateClient}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入客户用户名" />
          </Form.Item>
          
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          
          <Form.Item
            label="邮箱"
            name="email"
          >
            <Input placeholder="请输入邮箱地址（可选）" />
          </Form.Item>
          
          <Form.Item
            label="角色"
            name="role"
            initialValue="client"
          >
            <Select>
              <Select.Option value="client">客户</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="备注"
            name="remark"
          >
            <Input.TextArea placeholder="请输入备注信息（可选）" rows={3} />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={loading}
              >
                创建
              </Button>
              <Button 
                onClick={() => {
                  setCreateModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置API密钥确认模态框 */}
      <Modal
        title="重置API密钥"
        open={resetKeyModalVisible}
        onCancel={() => {
          setResetKeyModalVisible(false);
          setSelectedClient(null);
        }}
        onOk={handleResetApiKey}
      >
        <p>确定要为用户 <strong>{selectedClient?.username}</strong> 重置API密钥吗？</p>
        <p style={{ color: '#f56c6c' }}>此操作将生成新的API密钥，旧的密钥将失效。</p>
      </Modal>
    </div>
  );
}

  // 创建客户账户
  const handleCreateClient = async (values: any) => {
    try {
      const response = await clientsApiExtended.createClient(values);
      message.success('客户账户创建成功！');
      setCreateModalVisible(false);
      form.resetFields();
      fetchClients(); // 重新获取列表
      console.log('API密钥:', response.data.api_key); // 在实际应用中，可能需要展示API密钥给管理员
    } catch (error: any) {
      message.error('创建客户账户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 删除客户账户
  const handleDeleteClient = async (clientId: number) => {
    Modal.confirm({
      title: '确认删除客户',
      content: '确定要删除此客户账户吗？此操作将禁用该客户的访问权限。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await clientsApiExtended.deleteClient(clientId);
          message.success('客户账户删除成功！');
          fetchClients(); // 重新获取列表
        } catch (error: any) {
          message.error('删除客户账户失败: ' + (error.response?.data?.detail || error.message));
        }
      }
    });
  };

  // 重置API密钥
  const handleResetApiKey = async () => {
    if (!selectedClient) return;

    try {
      const response = await clientsApiExtended.resetApiKey(selectedClient.id);
      message.success('API密钥重置成功！');
      setResetKeyModalVisible(false);
      setSelectedClient(null);
      console.log('新API密钥:', response.data.api_key); // 在实际应用中，需要展示新API密钥
    } catch (error: any) {
      message.error('重置API密钥失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 搜索过滤
  const handleSearch = (value: string) => {
    if (!value.trim()) {
      setFilteredClients(clients);
      return;
    }
    
    const filtered = clients.filter(client => 
      client.username.toLowerCase().includes(value.toLowerCase()) ||
      (client.email && client.email.toLowerCase().includes(value.toLowerCase())) ||
      (client.remark && client.remark.toLowerCase().includes(value.toLowerCase()))
    );
    setFilteredClients(filtered);
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchClients();
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchClients();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a: ClientAccount, b: ClientAccount) => a.id - b.id,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      ellipsis: true,
      sorter: (a: ClientAccount, b: ClientAccount) => a.username.localeCompare(b.username),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => email || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {role}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Badge status={active ? 'success' : 'error'} text={active ? '激活' : '禁用'} />
      ),
      sorter: (a: ClientAccount, b: ClientAccount) => Number(a.is_active) - Number(b.is_active),
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      render: (remark: string) => remark || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: ClientAccount, b: ClientAccount) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ClientAccount) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<KeyOutlined />}
            onClick={() => {
              setSelectedClient(record);
              setResetKeyModalVisible(true);
            }}
          >
            重置密钥
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteClient(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>客户账户管理</Title>
      
      {/* 搜索和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search
            placeholder="搜索用户名、邮箱或备注"
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            onSearch={handleSearch}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 300 }}
          />
          <Button 
            type="primary" 
            icon={<UserAddOutlined />} 
            onClick={() => setCreateModalVisible(true)}
          >
            创建客户
          </Button>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 客户列表表格 - 自动填满剩余空间 */}
      <Card style={{ flex: 1, overflow: 'hidden' }}>
        <Table
          dataSource={filteredClients}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ y: 'calc(100vh - 300px)', x: 1000 }}
          style={{ height: '100%' }}
        />
      </Card>

      {/* 创建客户模态框 */}
      <Modal
        title="创建客户账户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateClient}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入客户用户名" />
          </Form.Item>
          
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          
          <Form.Item
            label="邮箱"
            name="email"
          >
            <Input placeholder="请输入邮箱地址（可选）" />
          </Form.Item>
          
          <Form.Item
            label="角色"
            name="role"
          >
            <Select defaultValue="client">
              <Select.Option value="client">客户</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="备注"
            name="remark"
          >
            <Input.TextArea placeholder="请输入备注信息（可选）" rows={3} />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={loading}
              >
                创建
              </Button>
              <Button 
                onClick={() => {
                  setCreateModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置API密钥确认模态框 */}
      <Modal
        title="重置API密钥"
        open={resetKeyModalVisible}
        onCancel={() => {
          setResetKeyModalVisible(false);
          setSelectedClient(null);
        }}
        onOk={handleResetApiKey}
      >
        <p>确定要为用户 <strong>{selectedClient?.username}</strong> 重置API密钥吗？</p>
        <p>此操作将生成新的API密钥，旧的密钥将失效。</p>
      </Modal>
    </div>
  );
}