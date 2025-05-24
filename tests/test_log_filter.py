#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 모듈: log_filter.py의 기능을 테스트합니다.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from log_filter import LogFilter, PatternManager, LogProcessor, PathResolver


class TestPatternManager(unittest.TestCase):
    """PatternManager 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 패턴 파일 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pattern_file = os.path.join(self.temp_dir.name, "test_patterns.json")
        
        # 테스트 패턴 데이터
        self.pattern_data = {
            "test_module": {
                "patterns": [
                    "pattern1",
                    "pattern2"
                ]
            }
        }
        
        # 패턴 파일 작성
        with open(self.pattern_file, "w", encoding="utf-8") as f:
            json.dump(self.pattern_data, f)
    
    def tearDown(self):
        """테스트 정리"""
        self.temp_dir.cleanup()
    
    def test_load_pattern_file(self):
        """패턴 파일 로드 테스트"""
        manager = PatternManager(self.pattern_file)
        self.assertEqual(manager.patterns_data, self.pattern_data)
    
    def test_get_module_patterns(self):
        """모듈 패턴 가져오기 테스트"""
        manager = PatternManager(self.pattern_file)
        patterns = manager.get_module_patterns("test_module")
        self.assertEqual(patterns, ["pattern1", "pattern2"])
    
    def test_module_not_found(self):
        """존재하지 않는 모듈 테스트"""
        manager = PatternManager(self.pattern_file)
        with self.assertRaises(KeyError):
            manager.get_module_patterns("non_existent_module")
    
    def test_extract_pattern_code(self):
        """패턴 코드 추출 테스트"""
        # 기본 패턴 파일
        code = PatternManager.extract_pattern_code("patterns.json")
        self.assertEqual(code, "default")
        
        # 접두사가 있는 패턴 파일
        code = PatternManager.extract_pattern_code("patterns_ABC.json")
        self.assertEqual(code, "ABC")
        
        # 다른 이름의 패턴 파일
        code = PatternManager.extract_pattern_code("custom_patterns.json")
        self.assertEqual(code, "custom_patterns")


class TestLogFilter(unittest.TestCase):
    """LogFilter 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 패턴 파일 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pattern_file = os.path.join(self.temp_dir.name, "test_patterns.json")
        
        # 테스트 패턴 데이터
        self.pattern_data = {
            "test_module": {
                "patterns": [
                    "^DEBUG:",
                    "^INFO: heartbeat$",
                    "\\d{3}-\\d{4}-\\d{4}"
                ]
            }
        }
        
        # 패턴 파일 작성
        with open(self.pattern_file, "w", encoding="utf-8") as f:
            json.dump(self.pattern_data, f)
            
        # LogFilter 인스턴스 생성
        self.log_filter = LogFilter("test_module", self.pattern_file)
    
    def tearDown(self):
        """테스트 정리"""
        self.temp_dir.cleanup()
    
    def test_should_exclude(self):
        """로그 라인 제외 여부 테스트"""
        # 제외되어야 하는 라인
        self.assertTrue(self.log_filter.should_exclude("DEBUG: test message"))
        self.assertTrue(self.log_filter.should_exclude("INFO: heartbeat"))
        self.assertTrue(self.log_filter.should_exclude("Contact: 010-1234-5678"))
        
        # 포함되어야 하는 라인
        self.assertFalse(self.log_filter.should_exclude("ERROR: test message"))
        self.assertFalse(self.log_filter.should_exclude("INFO: system started"))
        self.assertFalse(self.log_filter.should_exclude("Normal log line"))


class TestLogProcessor(unittest.TestCase):
    """LogProcessor 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 임시 패턴 파일 생성
        self.pattern_file = os.path.join(self.temp_dir.name, "test_patterns.json")
        self.pattern_data = {
            "test_module": {
                "patterns": [
                    "^DEBUG:",
                    "^INFO: heartbeat$"
                ]
            }
        }
        with open(self.pattern_file, "w", encoding="utf-8") as f:
            json.dump(self.pattern_data, f)
        
        # 임시 로그 파일 생성
        self.input_file = os.path.join(self.temp_dir.name, "input.log")
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write("DEBUG: test message\n")
            f.write("INFO: heartbeat\n")
            f.write("ERROR: test error\n")
            f.write("INFO: system started\n")
        
        # 출력 파일 경로
        self.output_file = os.path.join(self.temp_dir.name, "output.log")
        
        # LogFilter 및 LogProcessor 인스턴스 생성
        self.log_filter = LogFilter("test_module", self.pattern_file)
        self.log_processor = LogProcessor(self.log_filter)
    
    def tearDown(self):
        """테스트 정리"""
        self.temp_dir.cleanup()
    
    def test_process_file(self):
        """파일 처리 테스트"""
        # 파일 처리
        included_lines = self.log_processor.process_file(self.input_file, self.output_file)
        
        # 결과 확인
        self.assertEqual(included_lines, 2)  # 2개 라인이 포함되어야 함
        
        # 출력 파일 내용 확인
        with open(self.output_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("ERROR: test error", content)
        self.assertIn("INFO: system started", content)
        self.assertNotIn("DEBUG: test message", content)
        self.assertNotIn("INFO: heartbeat", content)


class TestPathResolver(unittest.TestCase):
    """PathResolver 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.base_dir = "/test/base/dir"
        self.path_resolver = PathResolver(self.base_dir)
    
    def test_resolve_input_path(self):
        """입력 경로 해석 테스트"""
        # 입력 파일이 None인 경우
        path = self.path_resolver.resolve_input_path(None, "test_module")
        self.assertEqual(path, "/test/base/dir/logs/test_module")
        
        # 입력 파일이 상대 경로인 경우
        path = self.path_resolver.resolve_input_path("custom.log", "test_module")
        self.assertEqual(path, "/test/base/dir/logs/custom.log")
        
        # 입력 파일이 절대 경로인 경우
        path = self.path_resolver.resolve_input_path("/absolute/path/file.log", "test_module")
        self.assertEqual(path, "/absolute/path/file.log")
    
    def test_generate_output_path(self):
        """출력 경로 생성 테스트"""
        # 출력 파일이 지정된 경우
        path = self.path_resolver.generate_output_path("output.log", "test_module", "default")
        self.assertEqual(path, "/test/base/dir/output.log")
        
        # 출력 파일이 절대 경로인 경우
        path = self.path_resolver.generate_output_path("/absolute/path/output.log", "test_module", "default")
        self.assertEqual(path, "/absolute/path/output.log")
        
        # 출력 파일이 None인 경우 (자동 생성)
        # 날짜에 의존하므로 경로 패턴만 확인
        path = self.path_resolver.generate_output_path(None, "test_module", "default")
        self.assertTrue(path.startswith("/test/base/dir/result/default/test_module/"))
        self.assertTrue("test_module_" in path)
        self.assertTrue(path.endswith(".log"))


if __name__ == "__main__":
    unittest.main()
