import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Tag, Typography, Input, Modal, Form, Select, message, Badge, Dropdown, Menu } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined, DatabaseOutlined, WarningOutlined } from '@ant-design/icons';
import { databaseApi } from '../api/client';
import { extractData, formatDateTime, getErrorMessage } from '../utils/helpers';

const { Title, Text } = Typography;

interface TableData {
  [key: string]: any;
}

interface TableInfo {
  name: string;
  rowCount: number;
}

export default function DatabaseManagement() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableData, setTableData] = useState<TableData[]>([]);
  const [loading, setLoading] = useState(false);
  const [databaseStatus, setDatabaseStatus] = useState<'connected' | 'disconnected' | 'loading'>('loading');
  const [databaseMessage, setDatabaseMessage] = useState('');
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingRow, setEditingRow] = useState<TableData | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [form] = Form.useForm();

  // 获取数据库表列表
  const fetchTables = async () => {
    try {
      setDatabaseStatus('loading');
      const response = await databaseApi.getTables();
      const data = extractData<TableInfo[]>(response);
      setTables(data);
      setDatabaseStatus('connected');
      setDatabaseMessage(`已连接，${data.length} 个表加载成功`);
      
      // 如果有表且未选择表，则默认选择第一个表
      if (data.length > 0 && !selectedTable) {
        setSelectedTable(data[0].name);
      }
    } catch (error) {
      setDatabaseStatus('disconnected');
      setDatabaseMessage('连接失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // 获取表数据
  const fetchTableData = async (tableName: string, page: number = 1, pageSize: number = pagination.pageSize) => {
    if (!tableName) return;
    
    try {
      setLoading(true);
      const response = await databaseApi.getTableData(tableName, { page, size: pageSize });
      const data = extractData<{ rows: TableData[]; total: number }>(response);
      
      // 更新表数据和分页信息
      setTableData(data.rows || data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: data.total || 0,
      }));
    } catch (error) {
      message.error('获取表数据失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };



  // 初始化数据库
  const handleInitializeDatabase = () => {
    Modal.confirm({
      title: '初始化数据库',
      content: '确定要初始化数据库吗？这将删除所有现有数据并重新创建表结构。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          setLoading(true);
          await databaseApi.initializeDatabase();
          message.success('数据库初始化成功！');
          fetchTables();
        } catch (error) {
          message.error('数据库初始化失败: ' + getErrorMessage(error));
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 清空数据库
  const handleClearDatabase = () => {
    Modal.confirm({
      title: '清空数据库',
      content: '确定要清空数据库吗？这将删除所有表中的数据，但保留表结构。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          setLoading(true);
          await databaseApi.clearDatabase();
          message.success('数据库清空成功！');
          fetchTables();
          if (selectedTable) {
            fetchTableData(selectedTable);
          }
        } catch (error) {
          message.error('数据库清空失败: ' + getErrorMessage(error));
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 新建记录
  const handleCreateRecord = () => {
    setEditingRow(null);
    form.resetFields();
    setEditModalVisible(true);
  };

  // 编辑记录
  const handleEditRecord = (record: TableData) => {
    setEditingRow(record);
    form.setFieldsValue(record);
    setEditModalVisible(true);
  };

  // 删除记录
  const handleDeleteRecord = (record: TableData) => {
    Modal.confirm({
      title: '删除记录',
      content: '确定要删除这条记录吗？',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          setLoading(true);
          // 假设每条记录都有id字段作为主键
          await databaseApi.deleteRecord(selectedTable, record.id);
          message.success('记录删除成功！');
          fetchTableData(selectedTable);
        } catch (error) {
          message.error('记录删除失败: ' + getErrorMessage(error));
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 保存记录
  const handleSaveRecord = async (values: any) => {
    try {
      setLoading(true);
      if (editingRow) {
        // 更新记录
        await databaseApi.updateRecord(selectedTable, editingRow.id, values);
        message.success('记录更新成功！');
      } else {
        // 创建记录
        await databaseApi.createRecord(selectedTable, values);
        message.success('记录创建成功！');
      }
      setEditModalVisible(false);
      fetchTableData(selectedTable);
    } catch (error) {
      message.error('保存记录失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchTables();
    if (selectedTable) {
      fetchTableData(selectedTable, pagination.current);
    }
  };

  // 处理分页变化
  const handlePaginationChange = (page: number, pageSize: number) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }));
    if (selectedTable) {
      fetchTableData(selectedTable, page, pageSize);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchTables();
  }, []);

  // 当选择的表变化时，获取表数据
  useEffect(() => {
    if (selectedTable) {
      fetchTableData(selectedTable);
    }
  }, [selectedTable]);

  // 生成表的列定义
  const generateColumns = (): ColumnsType<TableData> => {
    if (tableData.length === 0) return [];

    const firstRow = tableData[0];
    const columns: ColumnsType<TableData> = Object.keys(firstRow).map(key => {
      return {
        title: key,
        dataIndex: key,
        key,
        render: (text: any) => {
          // 特殊处理时间字段
          if (key.includes('created') || key.includes('updated') || key.includes('time')) {
            return text ? formatDateTime(text) : '-';
          }
          
          // 特殊处理布尔字段
          if (typeof firstRow[key] === 'boolean') {
            return <Badge status={text ? 'success' : 'error'} text={text ? '是' : '否'} />;
          }

          return text;
        },
      };
    });

    // 添加操作列
    columns.push({
      title: '操作',
      key: 'action',
      render: (_: any, record: TableData) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEditRecord(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => handleDeleteRecord(record)}
          >
            删除
          </Button>
        </Space>
      ),
    });

    return columns;
  };

  // 生成表单字段
  const generateFormItems = () => {
    if (tableData.length === 0) return [];

    const firstRow = tableData[0];
    return Object.keys(firstRow).map(key => {
      // 跳过id字段，因为它通常是自增的
      if (key === 'id' && !editingRow) {
        return null;
      }

      return (
        <Form.Item key={key} name={key} label={key}>
          {typeof firstRow[key] === 'boolean' ? (
            <Select>
              <Select.Option value={true}>是</Select.Option>
              <Select.Option value={false}>否</Select.Option>
            </Select>
          ) : (
            <Input placeholder={`请输入${key}`} />
          )}
        </Form.Item>
      );
    }).filter(Boolean);
  };

  // 表选择器的下拉菜单
  const tableMenu = (
    <Menu
      items={tables.map(table => ({
        key: table.name,
        label: (
          <Space>
            <Text>{table.name}</Text>
            <Tag>{table.rowCount} 行</Tag>
          </Space>
        ),
        onClick: () => setSelectedTable(table.name),
      }))}
    />
  );

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>
        <Space>
          <DatabaseOutlined /> SQLite数据库管理
        </Space>
      </Title>
      
      {/* 数据库状态和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space wrap>
              <Button 
                type="primary" 
                icon={<DatabaseOutlined />} 
                onClick={handleInitializeDatabase}
                loading={loading}
              >
                初始化数据库
              </Button>
              <Button 
                danger 
                icon={<WarningOutlined />} 
                onClick={handleClearDatabase}
                loading={loading}
              >
                清空数据库
              </Button>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={loading}
              >
                刷新
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={handleCreateRecord}
                disabled={!selectedTable}
                loading={loading}
              >
                新增记录
              </Button>
            </Space>
            <Space wrap>
              <Badge 
                status={databaseStatus === 'connected' ? 'success' : databaseStatus === 'disconnected' ? 'error' : 'processing'} 
                text={databaseMessage}
              />
              <Dropdown overlay={tableMenu} disabled={tables.length === 0}>
                <Button>
                  <Space>
                    {selectedTable || '选择表'}
                    {selectedTable && tables.find(t => t.name === selectedTable)?.rowCount && (
                      <Tag>{tables.find(t => t.name === selectedTable)?.rowCount} 行</Tag>
                    )}
                  </Space>
                </Button>
              </Dropdown>
            </Space>
          </Space>
        </Space>
      </Card>

      {/* 表数据展示 */}
      {selectedTable ? (
        <Card style={{ flex: 1, overflow: 'auto' }}>
          <Title level={4}>{selectedTable} 表</Title>
          <Table
            dataSource={tableData}
            columns={generateColumns()}
            rowKey="id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
              onChange: handlePaginationChange,
            }}
            scroll={{ y: 'calc(100vh - 350px)', x: 'max-content' }}
          />
        </Card>
      ) : (
        <Card style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Space direction="vertical" size="large" align="center">
            <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
            <Text type="secondary">请选择一个表查看数据</Text>
          </Space>
        </Card>
      )}

      {/* 编辑记录模态框 */}
      <Modal
        title={editingRow ? '编辑记录' : '新增记录'}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveRecord}
        >
          {generateFormItems()}
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={loading}
              >
                保存
              </Button>
              <Button 
                onClick={() => setEditModalVisible(false)}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
