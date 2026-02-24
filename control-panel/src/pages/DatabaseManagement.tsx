import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Tag, Typography, Input, Modal, Form, Tabs, message, Badge, Switch, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined, TeamOutlined, CopyOutlined } from '@ant-design/icons';
import { usersApi } from '../api/client';
import { extractData, formatDateTime, getErrorMessage } from '../utils/helpers';

const { Title, Text } = Typography;

interface AdminUser {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface ClientUser {
  id: number;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  api_key: string | null;
}

export default function UserManagement() {
  const [activeTab, setActiveTab] = useState<'admin' | 'client'>('admin');
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [clientUsers, setClientUsers] = useState<ClientUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | ClientUser | null>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [createForm] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  const fetchAdminUsers = async (page: number = 1, pageSize: number = pagination.pageSize) => {
    try {
      setLoading(true);
      const response = await usersApi.listAdmins(page, pageSize);
      const data = extractData<AdminUser[]>(response);
      setAdminUsers(data);
      setPagination(prev => ({ ...prev, current: page, pageSize, total: data.length }));
    } catch (error) {
      message.error('获取管理员用户列表失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const fetchClientUsers = async (page: number = 1, pageSize: number = pagination.pageSize) => {
    try {
      setLoading(true);
      const response = await usersApi.listClients(page, pageSize);
      const data = extractData<ClientUser[]>(response);
      setClientUsers(data);
      setPagination(prev => ({ ...prev, current: page, pageSize, total: data.length }));
    } catch (error) {
      message.error('获取客户用户列表失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAdmin = async (values: any) => {
    try {
      setLoading(true);
      await usersApi.createAdmin(values);
      message.success('管理员用户创建成功！');
      setCreateModalVisible(false);
      createForm.resetFields();
      fetchAdminUsers();
    } catch (error: any) {
      let errorMessage = getErrorMessage(error);
      if (errorMessage.includes('username') || errorMessage.includes('用户名')) {
        errorMessage = '用户名已存在，请使用其他用户名';
      } else if (errorMessage.includes('email') || errorMessage.includes('邮箱')) {
        errorMessage = '邮箱已存在，请使用其他邮箱';
      }
      message.error('创建失败: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async (values: any) => {
    try {
      setLoading(true);
      await usersApi.createClient(values);
      message.success('客户用户创建成功！');
      setCreateModalVisible(false);
      createForm.resetFields();
      fetchClientUsers();
    } catch (error: any) {
      let errorMessage = getErrorMessage(error);
      if (errorMessage.includes('username') || errorMessage.includes('用户名')) {
        errorMessage = '用户名已存在，请使用其他用户名';
      } else if (errorMessage.includes('email') || errorMessage.includes('邮箱')) {
        errorMessage = '邮箱已存在，请使用其他邮箱';
      }
      message.error('创建失败: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAdmin = async (values: any) => {
    if (!editingUser) return;
    try {
      setLoading(true);
      await usersApi.updateAdmin((editingUser as AdminUser).id, values);
      message.success('管理员用户更新成功！');
      setEditModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      fetchAdminUsers();
    } catch (error: any) {
      let errorMessage = getErrorMessage(error);
      if (errorMessage.includes('不能为空')) {
        if (errorMessage.includes('用户名')) {
          errorMessage = '用户名不能为空';
        } else if (errorMessage.includes('邮箱')) {
          errorMessage = '邮箱不能为空';
        }
      } else if (errorMessage.includes('username') || errorMessage.includes('用户名')) {
        errorMessage = '用户名已被其他用户使用，请使用其他用户名';
      } else if (errorMessage.includes('email') || errorMessage.includes('邮箱')) {
        errorMessage = '邮箱已被其他用户使用，请使用其他邮箱';
      }
      message.error('更新失败: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateClient = async (values: any) => {
    if (!editingUser) return;
    try {
      setLoading(true);
      await usersApi.updateClient((editingUser as ClientUser).id, values);
      message.success('客户用户更新成功！');
      setEditModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      fetchClientUsers();
    } catch (error: any) {
      let errorMessage = getErrorMessage(error);
      if (errorMessage.includes('不能为空')) {
        if (errorMessage.includes('用户名')) {
          errorMessage = '用户名不能为空';
        } else if (errorMessage.includes('邮箱')) {
          errorMessage = '邮箱不能为空';
        }
      } else if (errorMessage.includes('username') || errorMessage.includes('用户名')) {
        errorMessage = '用户名已被其他用户使用，请使用其他用户名';
      } else if (errorMessage.includes('email') || errorMessage.includes('邮箱')) {
        errorMessage = '邮箱已被其他用户使用，请使用其他邮箱';
      }
      message.error('更新失败: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAdmin = async (user: AdminUser) => {
    Modal.confirm({
      title: '删除管理员用户',
      content: `确定要删除管理员用户 "${user.username}" 吗？此操作无法恢复！`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          setLoading(true);
          await usersApi.deleteAdmin(user.id);
          message.success('删除成功！');
          fetchAdminUsers();
        } catch (error) {
          message.error('删除失败: ' + getErrorMessage(error));
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleDeleteClient = async (user: ClientUser) => {
    Modal.confirm({
      title: '删除客户用户',
      content: `确定要删除客户用户 "${user.username}" 吗？此操作无法恢复！`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          setLoading(true);
          await usersApi.deleteClient(user.id);
          message.success('删除成功！');
          fetchClientUsers();
        } catch (error) {
          message.error('删除失败: ' + getErrorMessage(error));
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleCopyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    message.success('API Key 已复制到剪贴板');
  };

  const adminColumns: ColumnsType<AdminUser> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 150,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: string) => <Tag color="blue">{role}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Badge status={isActive ? 'success' : 'error'} text={isActive ? '启用' : '禁用'} />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => formatDateTime(date),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 180,
      render: (date: string | null) => date ? formatDateTime(date) : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_: any, record: AdminUser) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingUser(record);
              form.setFieldsValue({
                username: record.username,
                email: record.email,
                role: record.role,
                is_active: record.is_active,
              });
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteAdmin(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const clientColumns: ColumnsType<ClientUser> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 150,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
      render: (email: string | null) => email || '-',
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      width: 250,
      render: (apiKey: string | null) => (
        apiKey ? (
          <Space>
            <Tooltip title={apiKey}>
              <Text code style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {apiKey}
              </Text>
            </Tooltip>
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopyApiKey(apiKey)}
            />
          </Space>
        ) : (
          <Text type="secondary">-</Text>
        )
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: string) => <Tag color="green">{role}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Badge status={isActive ? 'success' : 'error'} text={isActive ? '启用' : '禁用'} />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => formatDateTime(date),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 180,
      render: (date: string | null) => date ? formatDateTime(date) : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_: any, record: ClientUser) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingUser(record);
              form.setFieldsValue({
                username: record.username,
                email: record.email,
                role: record.role,
                is_active: record.is_active,
              });
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteClient(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    if (activeTab === 'admin') {
      fetchAdminUsers();
    } else {
      fetchClientUsers();
    }
  }, [activeTab]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>
        <Space>
          <UserOutlined /> 用户管理
        </Space>
      </Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => activeTab === 'admin' ? fetchAdminUsers() : fetchClientUsers()}
            loading={loading}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              createForm.resetFields();
              setCreateModalVisible(true);
            }}
          >
            {activeTab === 'admin' ? '新建管理员' : '新建客户'}
          </Button>
        </Space>
      </Card>

      <Card style={{ flex: 1, overflow: 'auto' }}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as 'admin' | 'client')}
          items={[
            {
              key: 'admin',
              label: (
                <Space>
                  <UserOutlined />
                  管理员用户
                  <Badge count={adminUsers.length} showZero />
                </Space>
              ),
              children: (
                <Table
                  dataSource={adminUsers}
                  columns={adminColumns}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 条记录`,
                    onChange: (page, pageSize) => {
                      setPagination(prev => ({ ...prev, current: page, pageSize }));
                      fetchAdminUsers(page, pageSize);
                    },
                  }}
                  scroll={{ y: 'calc(100vh - 350px)', x: 'max-content' }}
                />
              ),
            },
            {
              key: 'client',
              label: (
                <Space>
                  <TeamOutlined />
                  客户用户
                  <Badge count={clientUsers.length} showZero />
                </Space>
              ),
              children: (
                <Table
                  dataSource={clientUsers}
                  columns={clientColumns}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 条记录`,
                    onChange: (page, pageSize) => {
                      setPagination(prev => ({ ...prev, current: page, pageSize }));
                      fetchClientUsers(page, pageSize);
                    },
                  }}
                  scroll={{ y: 'calc(100vh - 350px)', x: 'max-content' }}
                />
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={activeTab === 'admin' ? '新建管理员' : '新建客户'}
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={activeTab === 'admin' ? handleCreateAdmin : handleCreateClient}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue={activeTab === 'admin' ? 'admin' : 'client'}>
            <Input disabled />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑用户"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={activeTab === 'admin' ? handleUpdateAdmin : handleUpdateClient}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item 
            name="email" 
            label="邮箱" 
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            label="新密码"
            rules={[
              { min: 6, message: '密码至少6个字符' },
            ]}
            tooltip="留空则不修改密码"
          >
            <Input.Password placeholder="留空则不修改密码" />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Input disabled />
          </Form.Item>
          <Form.Item name="is_active" label="状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}