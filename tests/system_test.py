# -*- coding: utf-8 -*-
"""
系统功能测试用例
验证各个模块的功能和集成
"""
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os

from src.common.config_manager import ConfigurationManager, get_config_manager
from src.common.performance_optimizer import PerformanceOptimizer, cache_result, measure_performance
from src.common.fault_tolerance import FaultToleranceManager, CircuitBreaker, ErrorType, execute_with_fault_tolerance
from src.services.session_service import SessionService
from src.services.llm_service import LLMService
from src.services.srs_service import SRSService
from src.services.tts_service import TTSService
from src.services.stt_service import STTService
from src.services.audio_processing_service import AudioProcessingService
from src.services.text_processing_service import TextProcessingService
from src.services.voice_call_service import VoiceCallService
from src.gateway.api_gateway import APIGateway


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        config_data = {
            "server": {
                "host": "localhost",
                "port": 8000
            },
            "llm": {
                "base_url": "https://test-api.com",
                "api_key": "test-key",
                "model": "test-model"
            },
            "tts": {
                "api_key": "test-tts-key"
            },
            "stt": {
                "api_key": "test-stt-key"
            },
            "semantic_retrieval": {
                "base_url": "http://test-srs.com",
                "api_key": "test-srs-key"
            }
        }
        json.dump(config_data, self.temp_config)
        self.temp_config.close()
    
    def tearDown(self):
        """测试后清理"""
        os.unlink(self.temp_config.name)
    
    def test_config_loading(self):
        """测试配置加载"""
        config_mgr = ConfigurationManager(self.temp_config.name)
        config = config_mgr.get_config()
        
        self.assertIsNotNone(config)
        self.assertEqual(config["server"]["host"], "localhost")
        self.assertEqual(config["llm"]["model"], "test-model")
    
    def test_config_validation(self):
        """测试配置验证"""
        config_mgr = ConfigurationManager(self.temp_config.name)
        validation_result = config_mgr.validate_config()
        
        self.assertTrue(validation_result["valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
    
    def test_get_config_by_key(self):
        """测试按键获取配置"""
        config_mgr = ConfigurationManager(self.temp_config.name)
        
        host = config_mgr.get_config_by_key("server", "host")
        self.assertEqual(host, "localhost")
        
        model = config_mgr.get_config_by_key("llm", "model")
        self.assertEqual(model, "test-model")


class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.optimizer = PerformanceOptimizer()
    
    @cache_result(ttl_seconds=1, max_size=100)
    async def cached_async_func(self, value):
        """带缓存的异步函数"""
        await asyncio.sleep(0.1)  # 模拟耗时操作
        return f"cached_{value}"
    
    @cache_result(ttl_seconds=1, max_size=100)
    def cached_sync_func(self, value):
        """带缓存的同步函数"""
        import time
        time.sleep(0.1)  # 模拟耗时操作
        return f"cached_{value}"
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 测试同步函数缓存
        result1 = self.cached_sync_func("test")
        result2 = self.cached_sync_func("test")
        
        self.assertEqual(result1, result2)
    
    async def test_async_cache_functionality(self):
        """测试异步缓存功能"""
        result1 = await self.cached_async_func("test")
        result2 = await self.cached_async_func("test")
        
        self.assertEqual(result1, result2)
    
    @measure_performance("test_operation")
    async def measured_async_func(self):
        """带性能测量的异步函数"""
        await asyncio.sleep(0.01)
        return "measured_result"
    
    @measure_performance("test_operation")
    def measured_sync_func(self):
        """带性能测量的同步函数"""
        import time
        time.sleep(0.01)
        return "measured_result"
    
    def test_performance_measurement(self):
        """测试性能测量"""
        result = self.measured_sync_func()
        self.assertEqual(result, "measured_result")
    
    async def test_async_performance_measurement(self):
        """测试异步性能测量"""
        result = await self.measured_async_func()
        self.assertEqual(result, "measured_result")


class TestFaultTolerance(unittest.TestCase):
    """容错机制测试"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = FaultToleranceManager()
    
    def test_circuit_breaker_functionality(self):
        """测试熔断器功能"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # 成功调用
        result = breaker.call(lambda: "success")
        self.assertEqual(result, "success")
        
        # 故障调用达到阈值后开启熔断器
        def failing_func():
            raise Exception("test failure")
        
        # 第一次失败
        try:
            breaker.call(failing_func)
        except:
            pass
        
        # 第二次失败，熔断器应该开启
        try:
            breaker.call(failing_func)
        except:
            pass
        
        # 现在应该被熔断
        with self.assertRaises(Exception) as context:
            breaker.call(lambda: "should_fail")
        
        self.assertIn("熔断器开启", str(context.exception))
    
    def test_error_classification(self):
        """测试错误分类"""
        handler = self.manager.error_handler
        
        # 测试超时错误分类
        timeout_error = handler._classify_error(Exception("timeout"))
        self.assertEqual(timeout_error, ErrorType.TIMEOUT_ERROR)
        
        # 测试网络错误分类
        network_error = handler._classify_error(Exception("connection error"))
        self.assertEqual(network_error, ErrorType.NETWORK_ERROR)
        
        # 测试客户端错误分类
        client_error = handler._classify_error(Exception("400 bad request"))
        self.assertEqual(client_error, ErrorType.CLIENT_ERROR)


class TestServices(unittest.TestCase):
    """服务模块测试"""
    
    def test_session_service(self):
        """测试会话服务"""
        session_service = SessionService()
        
        # 测试登录功能
        credentials = {"username": "123", "password": "123"}
        result = asyncio.run(session_service.login(credentials))
        
        self.assertEqual(result["code"], 200)
        self.assertIsNotNone(result["data"]["access_token"])
    
    def test_llm_service_initialization(self):
        """测试LLM服务初始化"""
        llm_service = LLMService()
        
        self.assertIsNotNone(llm_service)
        self.assertIsNotNone(llm_service.base_url)
        self.assertIsNotNone(llm_service.api_key)
    
    def test_srs_service_initialization(self):
        """测试SRS服务初始化"""
        srs_service = SRSService()
        
        self.assertIsNotNone(srs_service)
        self.assertIsNotNone(srs_service.base_url)
        self.assertIsNotNone(srs_service.api_key)
    
    def test_tts_service_initialization(self):
        """测试TTS服务初始化"""
        tts_service = TTSService()
        
        self.assertIsNotNone(tts_service)
    
    def test_stt_service_initialization(self):
        """测试STT服务初始化"""
        stt_service = STTService()
        
        self.assertIsNotNone(stt_service)
    
    def test_audio_processing_service_initialization(self):
        """测试音频处理服务初始化"""
        audio_service = AudioProcessingService()
        
        self.assertIsNotNone(audio_service)
    
    def test_text_processing_service_initialization(self):
        """测试文本处理服务初始化"""
        text_service = TextProcessingService()
        
        self.assertIsNotNone(text_service)
    
    def test_voice_call_service_initialization(self):
        """测试语音通话服务初始化"""
        voice_service = VoiceCallService()
        
        self.assertIsNotNone(voice_service)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_api_gateway_initialization(self):
        """测试API网关初始化"""
        gateway = APIGateway()
        
        self.assertIsNotNone(gateway)
        self.assertIsNotNone(gateway.app)
    
    def test_config_manager_singleton(self):
        """测试配置管理器单例模式"""
        config_mgr1 = get_config_manager()
        config_mgr2 = get_config_manager()
        
        self.assertIs(config_mgr1, config_mgr2)


class TestAsyncFunctionality(unittest.TestCase):
    """异步功能测试"""
    
    async def test_async_services(self):
        """测试异步服务功能"""
        # 测试会话服务异步方法
        session_service = SessionService()
        credentials = {"username": "123", "password": "123"}
        
        login_result = await session_service.login(credentials)
        self.assertEqual(login_result["code"], 200)
        
        # 获取用户信息
        if "data" in login_result and "access_token" in login_result["data"]:
            token = login_result["data"]["access_token"]
            user_info = await session_service.get_user_info(token)
            self.assertEqual(user_info["code"], 200)
    
    def test_run_async_tests(self):
        """运行异步测试"""
        asyncio.run(self.test_async_services())


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(unittest.makeSuite(TestConfigManager))
    suite.addTest(unittest.makeSuite(TestPerformanceOptimizer))
    suite.addTest(unittest.makeSuite(TestFaultTolerance))
    suite.addTest(unittest.makeSuite(TestServices))
    suite.addTest(unittest.makeSuite(TestIntegration))
    suite.addTest(unittest.makeSuite(TestAsyncFunctionality))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("开始运行系统功能测试...")
    test_result = run_all_tests()
    
    print(f"\n测试结果:")
    print(f"运行测试数: {test_result.testsRun}")
    print(f"失败数: {len(test_result.failures)}")
    print(f"错误数: {len(test_result.errors)}")
    print(f"成功率: {(test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun * 100:.2f}%")
    
    if test_result.failures:
        print("\n失败的测试:")
        for test, trace in test_result.failures:
            print(f"- {test}: {trace}")
    
    if test_result.errors:
        print("\n错误的测试:")
        for test, trace in test_result.errors:
            print(f"- {test}: {trace}")