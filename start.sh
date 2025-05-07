#!/bin/bash

# kubectx {cluster} or --kubeconfig {kubeconfig_path 지정}

kubectl logs -n {namespace} {moduleA_pod_name} --tail={tail_num} --timestamps > logs/{moduleA_name}
kubectl logs -n {namespace} {moduleB_pod_name} --tail={tail_num} --timestamps > logs/{moduleB_name}

python -u log_filter.py --module {moduleA}
python -u log_filter.py --module {moduleB} 

# python -u log_filter.py --module test --pattern-file patterns_BCD.json 패턴 파일 지정해서도 가능