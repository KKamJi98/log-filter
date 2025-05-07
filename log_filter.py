#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log_filter.py

프로젝트별 패턴 파일(a_patterns.json, b_patterns.json 등)을
--pattern-file 옵션으로 지정하여 사용할 수 있으며,
결과는 result/<pattern_code>/<module_name>/YYYY/MM/<module_name>_YYYYMMDD.log
형식으로 저장됩니다. patterns.json 사용 시 default 폴더에 저장됩니다.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# 스크립트 위치 기준으로 경로 설정
PATH = os.path.dirname(__file__)


class LogFilter:
    """
    지정된 JSON 파일에 정의된 정규표현식 패턴을 기반으로
    로그 라인에서 매칭되는 항목을 제외(exclude)하는 클래스
    """

    def __init__(self, module_name: str, pattern_file: str):
        """
        :param module_name: patterns 파일 내 키(모듈명)
        :param pattern_file: JSON 패턴 파일 경로
        """
        self.module_name = module_name
        self.pattern_file = pattern_file
        self.patterns = []
        self._load_patterns()

    def _load_patterns(self):
        """
        self.pattern_file에서 JSON을 로드한 후,
        self.module_name에 해당하는 패턴을 컴파일
        """
        try:
            with open(self.pattern_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 패턴 파일을 찾을 수 없습니다: {self.pattern_file}")
            sys.exit(1)

        if self.module_name not in data:
            print(f"⚠️ '{self.module_name}' 모듈에 대한 패턴이 없습니다.")
            sys.exit(1)

        raw_patterns = data[self.module_name].get("patterns", [])
        self.patterns = [re.compile(p) for p in raw_patterns]

    def should_exclude(self, log_line: str) -> bool:
        """
        :return: 로그 라인이 어떤 패턴과도 매칭되면 True(제외), 아니면 False(포함)
        """
        for pat in self.patterns:
            if pat.search(log_line):
                return True
        return False


def filter_logs(
    module_name: str, input_file: str, output_file: str, pattern_file: str
) -> None:
    """
    :param module_name: 모듈명 (patterns 키)
    :param input_file: 원본 로그 파일 경로
    :param output_file: 필터링 결과 파일 경로 (append 모드)
    :param pattern_file: 패턴 JSON 파일 경로
    """
    lf = LogFilter(module_name, pattern_file)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as fin, open(
        output_file, "a", encoding="utf-8"
    ) as fout:
        for line in fin:
            if not lf.should_exclude(line):
                fout.write(line)


def main():
    parser = argparse.ArgumentParser(
        description="로그 필터링 프로그램 (정규표현식 전용)"
    )
    parser.add_argument(
        "--module",
        required=True,
        help="적용할 모듈명 (patterns.json 또는 지정된 JSON의 키)",
    )
    parser.add_argument(
        "--input-file", default=None, help="필터링할 로그 파일명 (logs/ 하위 파일)"
    )
    parser.add_argument(
        "--output-file", default=None, help="결과 저장 파일 경로 (자동 생성 시 무시)"
    )
    parser.add_argument(
        "--pattern-file",
        default=os.path.join(PATH, "patterns.json"),
        help="필터링 패턴 JSON 파일 경로 (기본: patterns.json)",
    )
    args = parser.parse_args()

    # 입력 파일명 지정
    if args.input_file is None:
        args.input_file = args.module
    input_path = os.path.join(PATH, "logs", args.input_file)

    # 패턴 파일명에서 코드 추출
    base = os.path.basename(args.pattern_file)
    if base == "patterns.json":
        pattern_code = "default"
    else:
        m = re.match(r"patterns_(.+)\.json$", base)
        pattern_code = m.group(1) if m else os.path.splitext(base)[0]

    # 오늘 날짜 기준
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    ymd = now.strftime("%Y%m%d")

    # output-file 자동 생성
    if args.output_file is None:
        args.output_file = os.path.join(
            PATH,
            "result",
            pattern_code,
            args.module,
            year,
            month,
            f"{args.module}_{ymd}.log",
        )

    filter_logs(
        module_name=args.module,
        input_file=input_path,
        output_file=args.output_file,
        pattern_file=args.pattern_file,
    )

    print(f"✅ 필터링 결과를 '{args.output_file}'에 저장했습니다.")


if __name__ == "__main__":
    main()
