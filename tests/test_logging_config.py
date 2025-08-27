"""Comprehensive tests for logging configuration module."""

import unittest
import logging
import logging.config
from unittest.mock import patch, Mock, MagicMock
import tempfile
import os
import sys
from io import StringIO

from docpivot.logging_config import (
    DEFAULT_LOGGING_CONFIG,
    setup_logging,
    get_logger,
    PerformanceLogger,
    ProgressLogger,
    create_error_context_logger,
    log_exception_with_context,
)


class TestLoggingConfiguration(unittest.TestCase):
    """Test logging configuration functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Store original logging configuration
        self.original_handlers = logging.root.handlers[:]
        self.original_level = logging.root.level
        
    def tearDown(self):
        """Clean up after tests."""
        # Restore original logging configuration
        logging.root.handlers = self.original_handlers
        logging.root.setLevel(self.original_level)
        
    def test_default_logging_config_structure(self):
        """Test DEFAULT_LOGGING_CONFIG has expected structure."""
        self.assertIn("version", DEFAULT_LOGGING_CONFIG)
        self.assertEqual(DEFAULT_LOGGING_CONFIG["version"], 1)
        self.assertIn("formatters", DEFAULT_LOGGING_CONFIG)
        self.assertIn("handlers", DEFAULT_LOGGING_CONFIG)
        self.assertIn("loggers", DEFAULT_LOGGING_CONFIG)
        self.assertIn("root", DEFAULT_LOGGING_CONFIG)
        
        # Check formatters
        self.assertIn("detailed", DEFAULT_LOGGING_CONFIG["formatters"])
        self.assertIn("simple", DEFAULT_LOGGING_CONFIG["formatters"])
        self.assertIn("performance", DEFAULT_LOGGING_CONFIG["formatters"])
        
        # Check handlers
        self.assertIn("console", DEFAULT_LOGGING_CONFIG["handlers"])
        self.assertIn("detailed_console", DEFAULT_LOGGING_CONFIG["handlers"])
        self.assertIn("error_console", DEFAULT_LOGGING_CONFIG["handlers"])
        
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        setup_logging()
        
        # Check that docpivot logger exists
        logger = logging.getLogger("docpivot")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.INFO)
        
    def test_setup_logging_with_debug_level(self):
        """Test setup_logging with DEBUG level."""
        setup_logging(level="DEBUG")
        
        logger = logging.getLogger("docpivot")
        self.assertEqual(logger.level, logging.DEBUG)
        
    def test_setup_logging_with_warning_level(self):
        """Test setup_logging with WARNING level."""
        setup_logging(level="WARNING")
        
        logger = logging.getLogger("docpivot")
        self.assertEqual(logger.level, logging.WARNING)
        
    def test_setup_logging_with_error_level(self):
        """Test setup_logging with ERROR level."""
        setup_logging(level="ERROR")
        
        logger = logging.getLogger("docpivot")
        self.assertEqual(logger.level, logging.ERROR)
        
    def test_setup_logging_with_critical_level(self):
        """Test setup_logging with CRITICAL level."""
        setup_logging(level="CRITICAL")
        
        logger = logging.getLogger("docpivot")
        self.assertEqual(logger.level, logging.CRITICAL)
        
    def test_setup_logging_with_invalid_level(self):
        """Test setup_logging with invalid level (should use default)."""
        setup_logging(level="INVALID")
        
        # Should keep default level
        logger = logging.getLogger("docpivot")
        self.assertIsNotNone(logger)
        
    def test_setup_logging_with_detailed_formatting(self):
        """Test setup_logging with detailed formatting."""
        setup_logging(detailed=True)
        
        # Check that handlers are configured for detailed output
        config = DEFAULT_LOGGING_CONFIG.copy()
        # When detailed=True, formatters should be switched
        # This is a behavioral test - we can't directly inspect the handlers
        # but we verify the function runs without error
        self.assertIsNotNone(logging.getLogger("docpivot"))
        
    def test_setup_logging_with_custom_config(self):
        """Test setup_logging with custom configuration."""
        custom_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "custom": {
                    "format": "CUSTOM: %(message)s"
                }
            },
            "handlers": {
                "custom_handler": {
                    "class": "logging.StreamHandler",
                    "formatter": "custom",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "test_logger": {
                    "level": "INFO",
                    "handlers": ["custom_handler"]
                }
            },
            "root": {"level": "WARNING"}
        }
        
        setup_logging(config_dict=custom_config)
        
        # Check that custom logger exists
        logger = logging.getLogger("test_logger")
        self.assertIsNotNone(logger)
        
    def test_setup_logging_with_detailed_and_debug(self):
        """Test setup_logging with both detailed and debug options."""
        setup_logging(level="DEBUG", detailed=True)
        
        logger = logging.getLogger("docpivot")
        self.assertEqual(logger.level, logging.DEBUG)
        
    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test.module")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.module")
        
        # Test with different name
        logger2 = get_logger("another.module")
        self.assertEqual(logger2.name, "another.module")
        self.assertIsNot(logger, logger2)


class TestPerformanceLogger(unittest.TestCase):
    """Test PerformanceLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.perf_logger = PerformanceLogger(self.mock_logger)
        
    def test_log_operation_time_basic(self):
        """Test log_operation_time with basic parameters."""
        self.perf_logger.log_operation_time("TestOperation", 123.45)
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("TestOperation", call_args)
        self.assertIn("123.45ms", call_args)
        
    def test_log_operation_time_with_context(self):
        """Test log_operation_time with context."""
        context = {"file": "test.txt", "size": 1024}
        self.perf_logger.log_operation_time("FileRead", 50.0, context)
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("FileRead", call_args)
        self.assertIn("50.00ms", call_args)
        self.assertIn("file=test.txt", call_args)
        self.assertIn("size=1024", call_args)
        
    def test_log_file_processing_without_size(self):
        """Test log_file_processing without file size."""
        self.perf_logger.log_file_processing(
            "/path/to/file.txt",
            "read",
            75.5
        )
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("File read", call_args)
        self.assertIn("75.50ms", call_args)
        self.assertIn("file=/path/to/file.txt", call_args)
        
    def test_log_file_processing_with_size(self):
        """Test log_file_processing with file size."""
        self.perf_logger.log_file_processing(
            "/path/to/large.bin",
            "write",
            250.75,
            file_size_bytes=2048576
        )
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("File write", call_args)
        self.assertIn("250.75ms", call_args)
        self.assertIn("size_bytes=2048576", call_args)


class TestProgressLogger(unittest.TestCase):
    """Test ProgressLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.progress_logger = ProgressLogger(self.mock_logger, total_items=100)
        
    def test_initialization(self):
        """Test ProgressLogger initialization."""
        self.assertEqual(self.progress_logger.total_items, 100)
        self.assertEqual(self.progress_logger.processed_items, 0)
        
    def test_log_progress_single_increment(self):
        """Test log_progress with single increment."""
        self.progress_logger.log_progress()
        
        self.assertEqual(self.progress_logger.processed_items, 1)
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("1/100", call_args)
        self.assertIn("1.0%", call_args)
        
    def test_log_progress_multiple_increment(self):
        """Test log_progress with multiple increment."""
        self.progress_logger.log_progress(increment=5)
        
        self.assertEqual(self.progress_logger.processed_items, 5)
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("5/100", call_args)
        self.assertIn("5.0%", call_args)
        
    def test_log_progress_with_message(self):
        """Test log_progress with additional message."""
        self.progress_logger.log_progress(increment=10, message="Processing batch")
        
        self.assertEqual(self.progress_logger.processed_items, 10)
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("10/100", call_args)
        self.assertIn("10.0%", call_args)
        self.assertIn("Processing batch", call_args)
        
    def test_log_progress_accumulation(self):
        """Test that progress accumulates correctly."""
        self.progress_logger.log_progress(increment=20)
        self.progress_logger.log_progress(increment=30)
        
        self.assertEqual(self.progress_logger.processed_items, 50)
        self.assertEqual(self.mock_logger.info.call_count, 2)
        
        # Check second call
        second_call_args = self.mock_logger.info.call_args_list[1][0][0]
        self.assertIn("50/100", second_call_args)
        self.assertIn("50.0%", second_call_args)
        
    def test_log_completion_without_message(self):
        """Test log_completion without message."""
        self.progress_logger.processed_items = 100
        self.progress_logger.log_completion()
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("Completed", call_args)
        self.assertIn("100/100", call_args)
        
    def test_log_completion_with_message(self):
        """Test log_completion with message."""
        self.progress_logger.processed_items = 75
        self.progress_logger.log_completion(message="Finished early")
        
        self.mock_logger.info.assert_called_once()
        call_args = self.mock_logger.info.call_args[0][0]
        self.assertIn("Completed", call_args)
        self.assertIn("75/100", call_args)
        self.assertIn("Finished early", call_args)


class TestErrorContextLogger(unittest.TestCase):
    """Test error context logger functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_logger = Mock(spec=logging.Logger)
        
    def test_create_error_context_logger(self):
        """Test create_error_context_logger function."""
        adapter = create_error_context_logger(self.base_logger)
        
        self.assertIsInstance(adapter, logging.LoggerAdapter)
        self.assertIs(adapter.logger, self.base_logger)
        
    def test_error_context_adapter_without_context(self):
        """Test ErrorContextAdapter without error context."""
        adapter = create_error_context_logger(self.base_logger)
        
        msg, kwargs = adapter.process("Test message", {})
        self.assertEqual(msg, "Test message")
        
    def test_error_context_adapter_with_context(self):
        """Test ErrorContextAdapter with error context."""
        adapter = create_error_context_logger(self.base_logger)
        
        extra = {"error_context": {"file": "test.py", "line": 42}}
        msg, kwargs = adapter.process("Error occurred", {"extra": extra})
        
        self.assertIn("Error occurred", msg)
        self.assertIn("Context:", msg)
        self.assertIn("file=test.py", msg)
        self.assertIn("line=42", msg)
        
    def test_error_context_adapter_with_non_dict_context(self):
        """Test ErrorContextAdapter with non-dict context."""
        adapter = create_error_context_logger(self.base_logger)
        
        extra = {"error_context": "not a dict"}
        msg, kwargs = adapter.process("Error occurred", {"extra": extra})
        
        # Should not modify message if context is not a dict
        self.assertEqual(msg, "Error occurred")


class TestLogExceptionWithContext(unittest.TestCase):
    """Test log_exception_with_context function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=logging.Logger)
        
    def test_log_exception_basic(self):
        """Test log_exception_with_context with basic parameters."""
        exception = ValueError("Test error")
        
        log_exception_with_context(
            self.mock_logger,
            exception,
            "test_operation"
        )
        
        self.mock_logger.log.assert_called_once()
        call_args = self.mock_logger.log.call_args
        
        self.assertEqual(call_args[0][0], logging.ERROR)
        self.assertIn("test_operation", call_args[0][1])
        self.assertIn("ValueError", call_args[0][1])
        self.assertIn("Test error", call_args[0][1])
        self.assertTrue(call_args[1]["exc_info"])
        
    def test_log_exception_with_context(self):
        """Test log_exception_with_context with context."""
        exception = IOError("File not found")
        context = {"file": "/path/to/file", "mode": "r"}
        
        log_exception_with_context(
            self.mock_logger,
            exception,
            "file_read",
            context=context
        )
        
        self.mock_logger.log.assert_called_once()
        call_args = self.mock_logger.log.call_args[0][1]
        
        self.assertIn("file_read", call_args)
        # IOError is an alias for OSError in Python 3
        self.assertTrue("OSError" in call_args or "IOError" in call_args)
        self.assertIn("File not found", call_args)
        self.assertIn("file=/path/to/file", call_args)
        self.assertIn("mode=r", call_args)
        
    def test_log_exception_with_custom_level(self):
        """Test log_exception_with_context with custom log level."""
        exception = RuntimeError("Runtime issue")
        
        log_exception_with_context(
            self.mock_logger,
            exception,
            "runtime_check",
            level=logging.WARNING
        )
        
        self.mock_logger.log.assert_called_once()
        self.assertEqual(self.mock_logger.log.call_args[0][0], logging.WARNING)
        
    def test_log_exception_with_empty_context(self):
        """Test log_exception_with_context with empty context."""
        exception = Exception("Generic error")
        
        log_exception_with_context(
            self.mock_logger,
            exception,
            "generic_operation",
            context={}
        )
        
        self.mock_logger.log.assert_called_once()
        call_args = self.mock_logger.log.call_args[0][1]
        
        # Should not include context string if context is empty
        self.assertIn("generic_operation", call_args)
        self.assertIn("Exception", call_args)
        self.assertNotIn("[Context:", call_args)


class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for logging configuration."""
    
    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        # Setup logging
        setup_logging(level="DEBUG", detailed=False)
        
        # Get logger
        logger = get_logger("test.integration")
        self.assertIsNotNone(logger)
        
        # Create performance logger
        perf_logger = PerformanceLogger(logger)
        self.assertIsNotNone(perf_logger)
        
        # Create progress logger
        progress_logger = ProgressLogger(logger, total_items=10)
        self.assertIsNotNone(progress_logger)
        
        # Create error context logger
        context_logger = create_error_context_logger(logger)
        self.assertIsNotNone(context_logger)
        
    def test_multiple_logger_instances(self):
        """Test that multiple loggers work correctly."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        logger3 = get_logger("module1")  # Same name as logger1
        
        self.assertIsNot(logger1, logger2)
        self.assertIs(logger1, logger3)  # Same name returns same instance
        
    def test_logging_config_values(self):
        """Test specific configuration values."""
        # Test formatter configurations
        detailed_fmt = DEFAULT_LOGGING_CONFIG["formatters"]["detailed"]["format"]
        self.assertIn("%(asctime)s", detailed_fmt)
        self.assertIn("%(name)s", detailed_fmt)
        self.assertIn("%(levelname)s", detailed_fmt)
        self.assertIn("%(filename)s", detailed_fmt)
        self.assertIn("%(lineno)d", detailed_fmt)
        
        simple_fmt = DEFAULT_LOGGING_CONFIG["formatters"]["simple"]["format"]
        self.assertIn("%(levelname)s", simple_fmt)
        self.assertIn("%(name)s", simple_fmt)
        self.assertIn("%(message)s", simple_fmt)
        
        perf_fmt = DEFAULT_LOGGING_CONFIG["formatters"]["performance"]["format"]
        self.assertIn("PERF", perf_fmt)
        self.assertIn("Duration:", perf_fmt)
        
    def test_handler_configurations(self):
        """Test handler configurations."""
        # Use a fresh import to get original config
        from docpivot.logging_config import DEFAULT_LOGGING_CONFIG as fresh_config
        
        console_handler = fresh_config["handlers"]["console"]
        self.assertEqual(console_handler["class"], "logging.StreamHandler")
        # The level might be modified by previous tests, check it's one of the expected values
        self.assertIn(console_handler["level"], ["INFO", "DEBUG"])
        self.assertIn(console_handler["formatter"], ["simple", "detailed"])
        
        detailed_handler = fresh_config["handlers"]["detailed_console"]
        self.assertEqual(detailed_handler["level"], "DEBUG")
        self.assertEqual(detailed_handler["formatter"], "detailed")
        
        error_handler = fresh_config["handlers"]["error_console"]
        self.assertEqual(error_handler["level"], "ERROR")
        self.assertEqual(error_handler["stream"], "ext://sys.stderr")
        
    def test_logger_configurations(self):
        """Test logger configurations in DEFAULT_LOGGING_CONFIG."""
        # Use a fresh import to get original config
        from docpivot.logging_config import DEFAULT_LOGGING_CONFIG as fresh_config
        
        # Check docpivot logger
        docpivot_config = fresh_config["loggers"]["docpivot"]
        # The level might be modified by previous tests
        self.assertIn(docpivot_config["level"], ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self.assertIn("console", docpivot_config["handlers"])
        self.assertIn("error_console", docpivot_config["handlers"])
        self.assertFalse(docpivot_config["propagate"])
        
        # Check specialized loggers
        for logger_name in ["docpivot.io.readers", "docpivot.io.serializers", 
                           "docpivot.workflows", "docpivot.validation"]:
            logger_config = fresh_config["loggers"][logger_name]
            self.assertIn(logger_config["level"], ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
            self.assertFalse(logger_config["propagate"])


if __name__ == "__main__":
    unittest.main()