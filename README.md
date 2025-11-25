# K8s LLM Service (Ollama + FastAPI)

## 구성
- API: FastAPI + 정적 UI (`api/main.py`, `api/static/index.html`)
- Worker: Redis 큐 소비 후 Ollama 호출 (`worker/worker.py`)
- Redis: 큐/상태/결과/히스토리 저장
- Ollama: LLM 엔진

## 배포
- 로컬 Docker Compose: `docker-compose.yml`
- Kubernetes: `deployment.yaml` (ConfigMap, Redis/Ollama/API/Worker Deployments + api NodePort 30000)

## 최신 변경
- UI 리디자인 (인디고 테마) 및 히스토리에서 응답 요약 표시
- `/api/history`가 각 `job_id`의 결과를 함께 반환하도록 개선
- K8s 리소스/롤링 전략 조정 및 모델 스펙 변경(`OLLAMA_MODEL` 기본값을 작은 모델로 설정)
