import { RedoOutlined, SaveOutlined, SyncOutlined } from '@ant-design/icons';
import { Alert, Button, Card, Col, Divider, Form, InputNumber, message, Row, Space, Switch, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { sessionConfigApi } from '../api/client';

const { Title, Text } = Typography;

// 配置接口定义（暂使用any类型）

const SessionConfigPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [runtimeInfo, setRuntimeInfo] = useState<any>(null);
  const [sessionStats, setSessionStats] = useState<any>(null);

  // 加载当前配置
  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await sessionConfigApi.getCurrent();
      const data = response.data.data;
      if (data) {
        setRuntimeInfo(data.runtime_info);
        setSessionStats(data.session_stats);
        
        // 设置表单默认值
        form.setFieldsValue(data.current_config);
      }
      
      message.success('配置加载成功');
    } catch (error: any) {
      message.error('加载配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 保存配置
  const saveConfig = async (values: any) => {
    setSaving(true);
    try {
      const response = await sessionConfigApi.update(values);
      
      if (response.data.data && response.data.data.restart_required) {
        message.warning('配置已保存，但需要重启服务才能完全生效');
      } else {
        message.success('配置保存成功');
      }
      
      // 重新加载配置以获取最新状态
      await loadConfig();
    } catch (error: any) {
      message.error('保存配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // 重置为默认配置
  const resetToDefaults = async () => {
    try {
      await sessionConfigApi.resetDefaults();
      message.success('已重置为默认配置');
      await loadConfig();
    } catch (error: any) {
      message.error('重置配置失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 验证配置
  const validateConfig = async (values: any) => {
    try {
      const response = await sessionConfigApi.validate(values);
      if (response.data.data && response.data.data.is_valid) {
        message.success('配置验证通过');
        return true;
      } else if (response.data.data && response.data.data.errors) {
        message.error('配置验证失败: ' + response.data.data.errors.join(', '));
        return false;
      } else {
        message.error('配置验证失败: 无效的响应数据');
        return false;
      }
    } catch (error: any) {
      message.error('验证配置失败: ' + (error.response?.data?.detail || error.message));
      return false;
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={3}>会话配置</Title>
      
      <Row gutter={[24, 24]}>
        {/* 配置表单区域 */}
        <Col span={16}>
          <Card 
            title="会话参数配置" 
            loading={loading}
            extra={
              <Space>
                <Button 
                  icon={<SyncOutlined />} 
                  onClick={loadConfig}
                  disabled={loading}
                >
                  刷新
                </Button>
                <Button 
                  icon={<RedoOutlined />} 
                  onClick={resetToDefaults}
                  disabled={loading}
                >
                  重置默认
                </Button>
              </Space>
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={saveConfig}
              onFinishFailed={() => {
                message.error('表单验证失败，请检查输入');
              }}
            >
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="session_timeout_minutes"
                    label="会话总超时时间（分钟）"
                    rules={[
                      { required: true, message: '请输入会话超时时间' },
                      { type: 'number', min: 1, max: 1440, message: '请输入1-1440之间的数值' }
                    ]}
                  >
                    <InputNumber 
                      min={1} 
                      max={1440} 
                      style={{ width: '100%' }} 
                      placeholder="15"
                    />
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="inactivity_timeout_minutes"
                    label="不活跃超时时间（分钟）"
                    rules={[
                      { required: true, message: '请输入不活跃超时时间' },
                      { type: 'number', min: 1, max: 1440, message: '请输入1-1440之间的数值' }
                    ]}
                  >
                    <InputNumber 
                      min={1} 
                      max={1440} 
                      style={{ width: '100%' }} 
                      placeholder="5"
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="heartbeat_timeout_minutes"
                    label="心跳超时时间（分钟）"
                    rules={[
                      { required: true, message: '请输入心跳超时时间' },
                      { type: 'number', min: 1, max: 60, message: '请输入1-60之间的数值' }
                    ]}
                  >
                    <InputNumber 
                      min={1} 
                      max={60} 
                      style={{ width: '100%' }} 
                      placeholder="2"
                    />
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="cleanup_interval_seconds"
                    label="清理检查间隔（秒）"
                    rules={[
                      { required: true, message: '请输入清理间隔' },
                      { type: 'number', min: 10, max: 300, message: '请输入10-300之间的数值' }
                    ]}
                  >
                    <InputNumber 
                      min={10} 
                      max={300} 
                      style={{ width: '100%' }} 
                      placeholder="30"
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="deep_validation_interval_seconds"
                    label="深度验证间隔（秒）"
                    rules={[
                      { required: true, message: '请输入深度验证间隔' },
                      { type: 'number', min: 60, max: 3600, message: '请输入60-3600之间的数值' }
                    ]}
                  >
                    <InputNumber 
                      min={60} 
                      max={3600} 
                      style={{ width: '100%' }} 
                      placeholder="300"
                    />
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="log_level"
                    label="日志级别"
                    rules={[{ required: true, message: '请选择日志级别' }]}
                  >
                    <select style={{ width: '100%', height: 32, borderRadius: 6, border: '1px solid #d9d9d9' }}>
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="enable_auto_cleanup"
                    label="启用自动清理"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="enable_heartbeat_monitoring"
                    label="启用心跳监控"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    icon={<SaveOutlined />}
                    loading={saving}
                  >
                    保存配置
                  </Button>
                  <Button 
                    onClick={() => form.validateFields().then(validateConfig)}
                  >
                    验证配置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
        
        {/* 状态信息区域 */}
        <Col span={8}>
          <Card title="运行状态" loading={loading}>
            {runtimeInfo && (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>当前运行参数:</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">会话超时: </Text>
                    <Text>{runtimeInfo.session_timeout}</Text>
                  </div>
                  <div>
                    <Text type="secondary">不活跃超时: </Text>
                    <Text>{runtimeInfo.inactivity_timeout}</Text>
                  </div>
                  <div>
                    <Text type="secondary">心跳超时: </Text>
                    <Text>{runtimeInfo.heartbeat_timeout}</Text>
                  </div>
                  <div>
                    <Text type="secondary">清理间隔: </Text>
                    <Text>{runtimeInfo.cleanup_interval}</Text>
                  </div>
                  <div>
                    <Text type="secondary">深度验证间隔: </Text>
                    <Text>{runtimeInfo.deep_validation_interval}</Text>
                  </div>
                </div>
                
                <Divider />
                
                <div>
                  <Text strong>功能状态:</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">自动清理: </Text>
                    <Text type={runtimeInfo.auto_cleanup_enabled ? 'success' : 'danger'}>
                      {runtimeInfo.auto_cleanup_enabled ? '已启用' : '已禁用'}
                    </Text>
                  </div>
                  <div>
                    <Text type="secondary">心跳监控: </Text>
                    <Text type={runtimeInfo.heartbeat_monitoring_enabled ? 'success' : 'danger'}>
                      {runtimeInfo.heartbeat_monitoring_enabled ? '已启用' : '已禁用'}
                    </Text>
                  </div>
                </div>
              </>
            )}
          </Card>
          
          <Card title="会话统计" style={{ marginTop: 24 }} loading={loading}>
            {sessionStats && (
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">总会话数: </Text>
                  <Text strong>{sessionStats.total_sessions}</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">活跃会话: </Text>
                  <Text type="success">{sessionStats.active_sessions}</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">过期会话: </Text>
                  <Text type="warning">{sessionStats.expired_sessions}</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">断开会话: </Text>
                  <Text type="danger">{sessionStats.disconnected_sessions}</Text>
                </div>
                <div>
                  <Text type="secondary">待清理: </Text>
                  <Text type="danger">{sessionStats.cleanup_pending}</Text>
                </div>
              </div>
            )}
          </Card>
          
          <Alert
            style={{ marginTop: 24 }}
            message="配置说明"
            description={
              <div>
                <div>• <Text strong>会话总超时</Text>: 会话的最大存活时间</div>
                <div>• <Text strong>不活跃超时</Text>: 无活动后的清理时间</div>
                <div>• <Text strong>心跳超时</Text>: 心跳检测的容忍时间</div>
                <div>• <Text strong>清理间隔</Text>: 自动清理检查的频率</div>
                <div>• <Text strong>部分配置</Text>: 修改后需要重启服务才能完全生效</div>
              </div>
            }
            type="info"
            showIcon
          />
        </Col>
      </Row>
    </div>
  );
};

export default SessionConfigPage;