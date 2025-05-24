#!/bin/bash

# kubectx {cluster} or --kubeconfig {kubeconfig_path 지정}

kubectl logs -n {namespace} {moduleA_pod_name} --tail={tail_num} --timestamps > logs/{moduleA_name}
kubectl logs -n {namespace} {moduleB_pod_name} --tail={tail_num} --timestamps > logs/{moduleB_name}

# Poetry를 사용하여 실행
poetry run log-filter --module {moduleA}
poetry run log-filter --module {moduleB} 

# 패턴 파일 지정 예시
# poetry run log-filter --module test --pattern-file patterns_BCD.json

# 직접 실행 방식 (대체 방법)
# python -u log_filter.py --module {moduleA}
# python -u log_filter.py --module {moduleB} 