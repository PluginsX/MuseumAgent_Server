import { Button, Card, Form, Input, message, Modal, Popconfirm, Space, Switch, Table } from 'antd';
import { useEffect, useState } from 'react';
import { usersApi } from '../api/client';

export default function Users() {
  const [users, setUsers] = useState<{ id: number; username: string; email?: string; role: string; is_active: boolean }[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<Record<string, unknown> | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = () => {
    setLoading(true);
    usersApi.list()
      .then((r) => setUsers(r.data))  // 直接使用返回的数据，不需要包装在 users 属性中
      .catch((e: any) => {
        console.error('获取用户列表失败:', e);
        let errorMessage = '获取用户列表失败';
        if (e.response?.data?.detail) {
          errorMessage = e.response.data.detail;
        } else if (e.message) {
          errorMessage = e.message;
        }
        message.error(errorMessage);
      })
      .finally(() => setLoading(false));
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditUser = (record: typeof users[0]) => {
    setEditingUser(record);
    form.setFieldsValue({
      ...record,
      password: '', // 编辑时不显示原密码，但提供密码字段用于修改
    });
    setModalVisible(true);
  };

  const handleDeleteUser = (id: number) => {
    usersApi.delete(id)
      .then(() => {
        message.success('删除成功');
        loadUsers();
      })
      .catch((e: any) => {
        console.error('删除失败:', e);
        let errorMessage = '删除失败';
        if (e.response?.data?.detail) {
          errorMessage = e.response.data.detail;
        } else if (e.message) {
          errorMessage = e.message;
        }
        message.error(errorMessage);
      });
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingUser) {
        // 编辑用户时，只更新提供的字段
        const updateData: any = {};
        if (values.email !== undefined) updateData.email = values.email;
        if (values.role !== undefined) updateData.role = values.role;
        if (values.is_active !== undefined) updateData.is_active = values.is_active;
        // 如果提供了新密码，则更新密码
        if (values.password) {
          updateData.password = values.password;
        }
        
        await usersApi.update(editingUser.id as number, updateData);
        message.success('更新成功');
      } else {
        // 创建新用户时需要密码
        if (!values.password) {
          message.error('创建用户需要提供密码');
          return;
        }
        await usersApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadUsers();
    } catch (e: any) {
      console.error('保存失败:', e);
      console.log('错误对象详情:', e);
      console.log('错误响应:', e.response);
      console.log('错误数据:', e.response?.data);
      // 提取并显示具体的错误信息
      let errorMessage = '操作失败';
      if (e.response?.data?.detail) {
        errorMessage = e.response.data.detail;
        console.log('使用detail错误信息:', errorMessage);
      } else if (e.message) {
        errorMessage = e.message;
        console.log('使用message错误信息:', errorMessage);
      } else {
        console.log('使用默认错误信息:', errorMessage);
      }
      
      // 临时测试：同时使用alert和message
      alert('错误信息: ' + errorMessage);  // 这个应该总是显示
      message.error(errorMessage);  // 这个是我们要修复的
      console.log('message.error已调用，参数:', errorMessage);
    }
  };

  const toggleUserStatus = (userId: number, currentStatus: boolean) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      usersApi.update(userId, {
        email: user.email,
        role: user.role,
        is_active: !currentStatus,
      })
      .then(() => {
        message.success(`用户${!currentStatus ? '启用' : '禁用'}成功`);
        loadUsers(); // 重新加载用户列表
      })
      .catch((e: any) => {
        console.error('更新用户状态失败:', e);
        let errorMessage = '更新用户状态失败';
        if (e.response?.data?.detail) {
          errorMessage = e.response.data.detail;
        } else if (e.message) {
          errorMessage = e.message;
        }
        message.error(errorMessage);
      });
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    {
      title: '状态',
      key: 'is_active',
      render: (_: unknown, record: typeof users[0]) => (
        <Switch
          size="small"
          checked={record.is_active}
          onChange={(_) => toggleUserStatus(record.id, record.is_active)}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: typeof users[0]) => (
        <Space>
          <Button type="link" onClick={() => handleEditUser(record)}>编辑</Button>
          <Popconfirm
            title="确认删除用户"
            onConfirm={() => handleDeleteUser(record.id)}
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="用户管理"
        extra={
          <Button type="primary" onClick={handleCreateUser}>新建用户</Button>
        }
      >
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '新建用户'}
        open={modalVisible}
        onOk={handleOk}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          {!editingUser && (
            <>
              <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: !editingUser }]}>
                <Input.Password />
              </Form.Item>
            </>
          )}
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          {editingUser && (
            <Form.Item name="is_active" label="状态" valuePropName="checked">
              <Switch size="small" />
            </Form.Item>
          )}
          {editingUser && (
            <Form.Item name="password" label="新密码" help="留空则不修改密码">
              <Input.Password />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}