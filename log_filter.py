#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log_filter.py

정규표현식 패턴을 기반으로 로그 파일을 필터링하는 도구입니다.
지정된 패턴과 일치하는 로그 라인을 제외하고 새로운 로그만 출력합니다.

사용법:
    python log_filter.py --module <moduleName> [--input-file <file>] [--output-file <file>] [--pattern-file <file>]
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("log_filter")


class PatternManager:
    """패턴 파일을 관리하고 정규표현식 패턴을 로드하는 클래스"""

    def __init__(self, pattern_file: str):
        """
        패턴 관리자 초기화
        
        Args:
            pattern_file: JSON 패턴 파일 경로
        """
        self.pattern_file = pattern_file
        self.patterns_data = self._load_pattern_file()
        
    def _load_pattern_file(self) -> Dict:
        """
        패턴 파일에서 JSON 데이터를 로드
        
        Returns:
            Dict: 로드된 패턴 데이터
            
        Raises:
            FileNotFoundError: 패턴 파일을 찾을 수 없는 경우
            json.JSONDecodeError: JSON 형식이 잘못된 경우
        """
        try:
            with open(self.pattern_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"패턴 파일을 찾을 수 없습니다: {self.pattern_file}")
            raise
        except json.JSONDecodeError:
            logger.error(f"패턴 파일 형식이 잘못되었습니다: {self.pattern_file}")
            raise

    def get_module_patterns(self, module_name: str) -> List[str]:
        """
        지정된 모듈에 대한 패턴 목록을 반환
        
        Args:
            module_name: 모듈 이름 (패턴 파일의 키)
            
        Returns:
            List[str]: 정규표현식 패턴 목록
            
        Raises:
            KeyError: 모듈이 패턴 파일에 없는 경우
        """
        if module_name not in self.patterns_data:
            logger.error(f"'{module_name}' 모듈에 대한 패턴이 없습니다.")
            raise KeyError(f"Module '{module_name}' not found in pattern file")
        
        return self.patterns_data[module_name].get("patterns", [])
    
    def get_available_modules(self) -> List[str]:
        """
        사용 가능한 모듈 목록을 반환
        
        Returns:
            List[str]: 패턴 파일에 정의된 모듈 이름 목록
        """
        return list(self.patterns_data.keys())
    
    @staticmethod
    def extract_pattern_code(pattern_file: str) -> str:
        """
        패턴 파일 이름에서 패턴 코드를 추출
        
        Args:
            pattern_file: 패턴 파일 경로
            
        Returns:
            str: 추출된 패턴 코드 또는 'default'
        """
        base = os.path.basename(pattern_file)
        if base == "patterns.json":
            return "default"
        
        m = re.match(r"patterns_(.+)\.json$", base)
        return m.group(1) if m else os.path.splitext(base)[0]


class LogFilter:
    """
    정규표현식 패턴을 기반으로 로그 라인을 필터링하는 클래스
    """

    def __init__(self, module_name: str, pattern_file: str):
        """
        로그 필터 초기화
        
        Args:
            module_name: 모듈 이름 (패턴 파일의 키)
            pattern_file: JSON 패턴 파일 경로
        """
        self.module_name = module_name
        self.pattern_manager = PatternManager(pattern_file)
        self.patterns: List[Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """패턴 관리자에서 패턴을 로드하고 컴파일"""
        try:
            raw_patterns = self.pattern_manager.get_module_patterns(self.module_name)
            self.patterns = [re.compile(p) for p in raw_patterns]
            logger.info(f"'{self.module_name}' 모듈에 대해 {len(self.patterns)}개의 패턴을 로드했습니다.")
        except Exception as e:
            logger.error(f"패턴 컴파일 중 오류 발생: {str(e)}")
            raise

    def should_exclude(self, log_line: str) -> bool:
        """
        로그 라인이 제외되어야 하는지 확인
        
        Args:
            log_line: 검사할 로그 라인
            
        Returns:
            bool: 로그 라인이 어떤 패턴과도 매칭되면 True(제외), 아니면 False(포함)
        """
        for pat in self.patterns:
            if pat.search(log_line):
                return True
        return False


class LogProcessor:
    """로그 파일을 처리하고 필터링하는 클래스"""
    
    def __init__(self, log_filter: LogFilter):
        """
        로그 프로세서 초기화
        
        Args:
            log_filter: 사용할 LogFilter 인스턴스
        """
        self.log_filter = log_filter
        
    def process_file(self, input_file: str, output_file: str) -> int:
        """
        입력 파일을 처리하고 필터링된 결과를 출력 파일에 저장
        
        Args:
            input_file: 입력 로그 파일 경로
            output_file: 출력 파일 경로
            
        Returns:
            int: 필터링되지 않은(포함된) 라인 수
            
        Raises:
            FileNotFoundError: 입력 파일을 찾을 수 없는 경우
            IOError: 파일 읽기/쓰기 오류 발생 시
        """
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        included_lines = 0
        
        try:
            with open(input_file, "r", encoding="utf-8") as fin:
                with open(output_file, "a", encoding="utf-8") as fout:
                    for line in fin:
                        if not self.log_filter.should_exclude(line):
                            fout.write(line)
                            included_lines += 1
                            
            logger.info(f"총 {included_lines}개의 라인이 필터링되지 않고 포함되었습니다.")
            return included_lines
            
        except FileNotFoundError:
            logger.error(f"입력 파일을 찾을 수 없습니다: {input_file}")
            raise
        except IOError as e:
            logger.error(f"파일 처리 중 오류 발생: {str(e)}")
            raise


class PathResolver:
    """파일 경로를 해석하고 생성하는 클래스"""
    
    def __init__(self, base_dir: str):
        """
        경로 해석기 초기화
        
        Args:
            base_dir: 기본 디렉토리 경로
        """
        self.base_dir = base_dir
        
    def resolve_input_path(self, input_file: Optional[str], module_name: str) -> str:
        """
        입력 파일 경로 해석
        
        Args:
            input_file: 입력 파일 이름 또는 None
            module_name: 모듈 이름
            
        Returns:
            str: 해석된 입력 파일 경로
        """
        if input_file is None:
            input_file = module_name
        
        # 절대 경로인 경우 그대로 반환
        if os.path.isabs(input_file):
            return input_file
            
        return os.path.join(self.base_dir, "logs", input_file)
        
    def generate_output_path(
        self, 
        output_file: Optional[str], 
        module_name: str, 
        pattern_code: str
    ) -> str:
        """
        출력 파일 경로 생성
        
        Args:
            output_file: 출력 파일 경로 또는 None
            module_name: 모듈 이름
            pattern_code: 패턴 코드
            
        Returns:
            str: 생성된 출력 파일 경로
        """
        if output_file is not None:
            # 절대 경로인 경우 그대로 반환
            if os.path.isabs(output_file):
                return output_file
            return os.path.join(self.base_dir, output_file)
            
        # 현재 날짜 기준으로 경로 생성
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        ymd = now.strftime("%Y%m%d")
        
        return os.path.join(
            self.base_dir,
            "result",
            pattern_code,
            module_name,
            year,
            month,
            f"{module_name}_{ymd}.log",
        )


def parse_arguments():
    """
    명령줄 인수 파싱
    
    Returns:
        argparse.Namespace: 파싱된 인수
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(
        description="로그 필터링 프로그램 (정규표현식 전용)"
    )
    parser.add_argument(
        "--module",
        required=True,
        help="적용할 모듈명 (patterns.json 또는 지정된 JSON의 키)",
    )
    parser.add_argument(
        "--input-file", 
        default=None, 
        help="필터링할 로그 파일명 (logs/ 하위 파일 또는 절대 경로)"
    )
    parser.add_argument(
        "--output-file", 
        default=None, 
        help="결과 저장 파일 경로 (자동 생성 시 무시)"
    )
    parser.add_argument(
        "--pattern-file",
        default=os.path.join(base_dir, "patterns.json"),
        help="필터링 패턴 JSON 파일 경로 (기본: patterns.json)",
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="상세 로깅 활성화"
    )
    
    return parser.parse_args()


def main():
    """메인 함수"""
    # 인수 파싱
    args = parse_arguments()
    
    # 로깅 레벨 설정
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # 패턴 코드 추출
        pattern_code = PatternManager.extract_pattern_code(args.pattern_file)
        
        # 경로 해석기 생성
        path_resolver = PathResolver(base_dir)
        
        # 입력 및 출력 경로 해석
        input_path = path_resolver.resolve_input_path(args.input_file, args.module)
        output_path = path_resolver.generate_output_path(
            args.output_file, args.module, pattern_code
        )
        
        logger.debug(f"입력 파일: {input_path}")
        logger.debug(f"출력 파일: {output_path}")
        logger.debug(f"패턴 파일: {args.pattern_file}")
        
        # 로그 필터 생성
        log_filter = LogFilter(args.module, args.pattern_file)
        
        # 로그 프로세서 생성 및 실행
        processor = LogProcessor(log_filter)
        included_lines = processor.process_file(input_path, output_path)
        
        logger.info(f"✅ 필터링 결과를 '{output_path}'에 저장했습니다. ({included_lines}개 라인 포함)")
        
    except KeyError as e:
        logger.error(f"모듈 오류: {str(e)}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"파일 오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
