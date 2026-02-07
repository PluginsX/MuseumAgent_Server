"""客户端异常类定义"""


class ClientError(Exception):
    """客户端错误基类"""
    pass


class APIError(ClientError):
    """API错误
    
    Attributes:
        status_code: HTTP状态码
        message: 错误消息
        details: 错误详情
    """
    
    def __init__(self, status_code, message, details=None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"API Error ({status_code}): {message}")


class ConnectionError(ClientError):
    """连接错误"""
    pass


class TimeoutError(ClientError):
    """超时错误"""
    pass
