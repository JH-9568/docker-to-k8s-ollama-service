# Ollama LLM Service

**추론 요청 하나를, 컨테이너와 클러스터의 처리 흐름으로.**

FastAPI·Redis·Ollama로 만든 비동기 LLM 서비스입니다. 요청 API와 추론 워커를 분리하고, 같은 구성을 Docker Compose에서 Kubernetes로 옮겨보는 인프라 프로젝트입니다.

[프로젝트 소개](https://jinhyeong-studio.jinhyeong9568-663.workers.dev/projects/ollama-service)

## 요청이 처리되는 과정

```text
Web UI → FastAPI → Redis Queue → Worker → Ollama
             ↑                     │
             └── 상태·결과 조회 ←── Redis
```

- API는 작업 ID를 반환하고 클라이언트는 상태를 조회합니다.
- 워커는 Redis 큐에서 작업을 가져와 Ollama의 `/api/generate`를 호출합니다.
- 결과와 상태에는 1시간 TTL을 적용합니다.
- 웹 UI는 최근 요청 10개와 응답을 보여줍니다.

## 실행 · Docker Compose

Docker가 필요하며 첫 실행에는 모델 다운로드 시간이 걸립니다.

```bash
docker compose up -d
```

API·웹 UI: `http://localhost:8000` · Ollama: `http://localhost:11434`  
기본 모델: `llama3.2:1b`

## 실행 · Kubernetes

```bash
kubectl apply -f deployment.yaml
minikube service api-service --url
```

매니페스트에는 API 2개·워커 3개 replica 구성이 있습니다. 이는 배포 설정이며, 실제 클러스터가 상시 운영된다는 뜻은 아닙니다.

## 기술과 학습 범위

| 구성 | 역할 |
| --- | --- |
| FastAPI | 요청 접수·작업 상태·결과 API |
| Redis | 작업 큐와 임시 상태 저장 |
| Worker | 큐 소비와 모델 호출 |
| Ollama | 로컬 모델 추론 |
| Docker Compose / Kubernetes | 로컬 통합 실행과 배포 구성 |

현재 큐는 `LPUSH / BRPOP` 기반 데모입니다. 단일 Redis·Ollama 구성으로, 고가용성·정확히 한 번 처리·장애 시 재시도 보장을 구현했다고 주장하지 않습니다. 웹 결과 조회에도 대기 시간 제한이 있습니다.
