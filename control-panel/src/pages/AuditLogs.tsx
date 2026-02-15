import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Tag, Typography, Input, DatePicker, message, Select } from 'antd';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { clientsApiExtended } from '../api/client';
import { extractData, formatDateTime, getErrorMessage } from '../utils/helpers';
import type { AuditLog } from '../types';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

export default function AuditLogs() {
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filters, setFilters] = useState<any>({});

  // 获取审计日志
  const fetchLogs = async (page: number = 1, currentFilters: any = {}) => {
    try {
      setLoading(true);
      const params: any = {
        page,
        size: pagination.pageSize,
        ...currentFilters
      };
      
      // 如果有时间范围，则格式化日期
      if (params.dateRange) {
        params.start_time = params.dateRange[0].toISOString();
        params.end_time = params.dateRange[1].toISOString();
        delete params.dateRange;
      }

      const response = await clientsApiExtended.getAuditLogs(params);
      const data = extractData<{ logs: AuditLog[]; pagination: any }>(response);
      
      setFilteredLogs(data.logs || []);
      setPagination({
        current: data.pagination?.page || page,
        pageSize: data.pagination?.size || pagination.pageSize,
        total: data.pagination?.total || 0,
      });
    } catch (error) {
      message.error('获取审计日志失败: ' + getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // 搜索过滤
  const handleSearch = (newFilters: any) => {
    setFilters(newFilters);
    fetchLogs(1, newFilters);
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchLogs(pagination.current, filters);
  };

  // 分页变化处理
  const handlePageChange = (page: number) => {
    fetchLogs(page, filters);
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchLogs();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a: AuditLog, b: AuditLog) => a.id - b.id,
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      render: (userId?: number) => userId || '-',
      width: 100,
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => (
        <Tag color={
          action.includes('LOGIN') ? 'blue' :
          action.includes('CREATE') ? 'green' :
          action.includes('DELETE') ? 'red' :
          action.includes('RESET') ? 'orange' :
          'default'
        }>
          {action}
        </Tag>
      ),
      width: 150,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip?: string) => ip || '-',
      width: 130,
    },
    {
      title: '详细信息',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatDateTime(date),
      sorter: (a: AuditLog, b: AuditLog) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      width: 180,
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Title level={3}>审计日志</Title>
      
      {/* 搜索和筛选栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space wrap>
            <Select
              placeholder="操作类型"
              style={{ width: 200 }}
              allowClear
              options={[
                { label: '登录成功', value: 'LOGIN_SUCCESS' },
                { label: '登录失败', value: 'LOGIN_FAILED' },
                { label: '创建客户', value: 'CLIENT_CREATE' },
                { label: '删除客户', value: 'CLIENT_DELETE' },
                { label: '重置密钥', value: 'API_KEY_RESET' },
              ]}
              onChange={(value) => handleSearch({ ...filters, action: value })}
            />
            <Input
              placeholder="用户ID"
              style={{ width: 150 }}
              onPressEnter={(e) => handleSearch({ ...filters, user_id: e.currentTarget.value })}
            />
            <RangePicker
              showTime
              format="YYYY-MM-DD HH:mm:ss"
              placeholder={['开始时间', '结束时间']}
              onChange={(dates) => handleSearch({ ...filters, dateRange: dates })}
            />
            <Button 
              type="primary" 
              icon={<SearchOutlined />} 
              onClick={() => handleSearch(filters)}
            >
              搜索
            </Button>
          </Space>
          <Space>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={handleRefresh}
              loading={loading}
            >
              刷新
            </Button>
            <Text type="secondary">
              共 {pagination.total} 条日志记录
            </Text>
          </Space>
        </Space>
      </Card>

      {/* 日志列表表格 */}
      <Card style={{ flex: 1, overflow: 'hidden' }}>
        <Table
          dataSource={filteredLogs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            onChange: handlePageChange,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ y: 'calc(100vh - 350px)', x: 1000 }}
          style={{ height: '100%' }}
        />
      </Card>
    </div>
  );
}