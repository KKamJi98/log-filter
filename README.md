# log-filter

Log Filter는 patterns.json에 정의된 모듈별 정규표현식 패턴을 기반으로 추가된 로그를 제외하고 새로운 로그만 확인할 수 있도록 도와주는 Python Tool 입니다. 대량의 로그에서 새로운 패턴의 로그를 빠르게 분류해서 확인할 수 있습니다.

***패턴을 추가해두면, 해당 패턴이 포함된 라인은 결과에서 제외됩니다.**

## Major Functions

- 정규표현식 전용 필터링: patterns.json에 등록된 모든 패턴을 정규표현식으로 처리하여 정확하고 유연한 매칭 지원
- 모듈별 패턴 관리: 모듈 이름을 키로 구분하여 JSON 구조로 패턴을 분리 관리
- 기존 결과 유지: 출력 파일이 이미 존재하면 기존 내용을 유지하고 새로운 결과를 append 모드로 추가
- 자동 디렉터리 생성: 결과 저장 경로의 디렉터리를 자동으로 생성
- 로깅 시스템: 상세한 로깅을 통한 디버깅 및 모니터링 지원
- 확장 가능한 구조: 모듈화된 설계로 새로운 기능 추가 용이

## Directory Structure

```shell
log-filter/
├── patterns.json        # 기본 필터링 패턴 정의 파일
├── patterns_*.json      # 추가 패턴 정의 파일들
├── log_filter.py        # 메인 스크립트
├── logs/                # 원본 로그 파일 디렉터리
│   └── example.log      # 예시 로그 파일
├── result/              # 필터링 결과 저장 디렉터리
└── tests/               # 테스트 코드 디렉터리
    └── test_log_filter.py  # 단위 테스트
```

## 설치 및 실행 방법

### 1. Clone Repository

```shell
git clone https://github.com/KKamJi98/log-filter.git
cd log-filter
```

### 2. 의존성 설치 (테스트용)

```shell
pip install -r requirements.txt
```

### 3. patterns.json 파일에 필터 패턴 설정

patterns.json 예시

```json
{
  "moduleA": {
    "patterns": [
      "\\(\\d{5}\\)",
      "\\[\\+\\d+\\]",      
      "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d+Z\\s*$",  
      "INFO"
    ]
  }
}
```

1. (12345) 형태 필터링
2. [+123] 형태 필터링
3. 타임스탬프만 있는 라인 필터링
4. INFO레벨 로그 필터링

### 4. Log Filter 실행

```shell
python log_filter.py --module <moduleName> [--input-file <file>] [--output-file <file>] [--pattern-file <file>] [--verbose]

--module: patterns.json 키와 일치하는 모듈명 (required)
--input-file: 필터링할 로그 파일 경로 (optional - 생략 시 `./logs/{module_name}` 참조)
--output-file: 결과 저장 파일 경로 (optional - 생략 시 `./result/default/{module_name}/YY/MM/{module_name}_YYYYMMDD.logs` 자동 생성)
--pattern-file: 패턴파일 지정 가능 (optional - 생략 시 `patterns.json` 참조)
--verbose: 상세 로깅 활성화 (optional)
```

## 사용 예시

```shell
# 가장 단순한 형태 (입력 생략 시 logs/moduleA 사용)
python log_filter.py --module moduleA

# 입력 로그 파일 명시
python log_filter.py --module moduleA --input-file logs/app.log

# 결과 파일도 직접 지정
python log_filter.py --module moduleA --input-file logs/app.log --output-file result/moduleA/output.log

# 패턴 파일도 지정 (기본 patterns.json 외 patterns_ABC.json 사용 예)
python log_filter.py --pattern-file patterns_ABC.json --module moduleA --input-file logs/app.log --output-file result/moduleA/output.log

# 상세 로깅 활성화
python log_filter.py --module moduleA --verbose
```

## 테스트 실행

```shell
# 모든 테스트 실행
pytest

# 테스트 커버리지 확인
pytest --cov=.
```

## 확장 방법

### 새로운 패턴 파일 추가

1. `patterns_<name>.json` 형식으로 새 패턴 파일 생성
2. JSON 구조로 모듈별 패턴 정의
3. `--pattern-file` 옵션으로 새 패턴 파일 지정

### 코드 확장

코드는 다음과 같은 클래스로 모듈화되어 있어 쉽게 확장 가능합니다:

- `PatternManager`: 패턴 파일 관리
- `LogFilter`: 로그 필터링 로직
- `LogProcessor`: 로그 파일 처리
- `PathResolver`: 파일 경로 해석 및 생성

## 라이센스

MIT License
