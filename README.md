# LLM Service (Docker Compose + Kubernetes)

FastAPI API + 정적 UI → Redis 큐 → Worker → Ollama → Redis 결과 → API 폴링 응답.  
Docker Compose로 로컬 실행, Kubernetes로 멀티 파드 통신을 데모/배포합니다.

## 통신 흐름
- 브라우저: `/api/run` POST → `job_id` 수신 → `/api/result/{job_id}` 폴링, `/api/history`로 최근 요청/응답 요약 표시.
- API(`api/main.py`): Redis 리스트 `prompthub:jobs`에 job push, 상태 키 `prompthub:status:{job}`, 결과 키 `prompthub:result:{job}` 조회/응답. 히스토리 리스트 `prompthub:history`에 최대 10개 저장(프롬프트+결과 요약).
- Worker(`worker/worker.py`): `BRPOP prompthub:jobs` → Ollama(`/api/generate`) 호출 → 결과/상태를 Redis에 저장.
- Redis: 큐/상태/결과/히스토리 저장소.
- Ollama: LLM 엔진(기본 `OLLAMA_MODEL=llama3.2:1b`).

## Docker Compose 버전 (`docker-compose.yml`)
- Services: `redis`, `api`, `worker`, `ollama`.
- 로컬 포트: API 8000, Redis 6379, Ollama 11434.
- 기본 설정: worker가 Ollama provider 사용, 결과 TTL 3600초.
- 실행
  ```bash
  docker compose up -d
  open http://localhost:8000   # 프런트/UI
  ```

## Kubernetes 버전 (`deployment.yaml`)
- 리소스: ConfigMap + Deployments(redis, ollama, api, worker) + Services(redis, ollama, api-service NodePort 30000).
- Ollama: requests 2 CPU / 4Gi, limit 6Gi, rollingUpdate(maxSurge 0, maxUnavailable 1).
- API replicas 2, Worker replicas 3.
- 실행
  ```bash
  kubectl apply -f deployment.yaml
  minikube service api-service --url   # 또는 http://<minikube-ip>:30000
  ```

## UI/기능 포인트
- 인디고 테마 카드형 UI, 상태바/결과 영역 분리.
- 히스토리에서 프롬프트와 응답 요약(최대 140자) 동시 표시.
- 결과 폴링 타임아웃 240초, 에러 시 상태/결과 영역에 표시.

## 최근 변경
- UI 리디자인 및 히스토리 응답 요약 표시 추가.
- `/api/history`가 job 결과를 함께 반환하도록 개선.
- K8s 리소스/롤링 전략 조정, 기본 모델을 작은 사이즈로 설정.
