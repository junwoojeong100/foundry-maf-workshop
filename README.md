# Microsoft Foundry & Microsoft Agent Framework 핸즈온 워크샵

> AI 에이전트를 **만들고(Foundry)**, **코드로 빌드(Agent Framework)** 하는 기본기를 약 2.5시간 안에 익히는 실습 워크샵입니다.

이 워크샵은 처음 Microsoft의 에이전트 스택을 접하는 개발자를 대상으로 합니다. 아주 기본적이지만 **꼭 알아야 하는 것들**만 골라, 직접 손으로 따라 하며 개념을 몸에 익히도록 구성했습니다.

---

## 🎯 학습 목표

이 워크샵을 마치면 다음을 할 수 있습니다.

- Microsoft Foundry와 Microsoft Agent Framework가 **각각 무엇이고 어떻게 다른지** 설명할 수 있다.
- Foundry 포털에서 **프로젝트를 만들고 모델을 배포**할 수 있다.
- Foundry SDK로 배포된 **모델을 코드로 호출**할 수 있다.
- Agent Framework로 **코드 몇 줄만에 에이전트를 만들고**, **도구(함수)를 붙이고**, **워크플로우로 연결**할 수 있다.
- 만든 에이전트·워크플로우를 **Foundry에 hosted agent로 배포**하고 이름으로 호출할 수 있다.

---

## 🧭 Foundry vs Agent Framework — 한눈에 정리

두 이름이 헷갈리기 쉽습니다. 관계를 먼저 정리하고 시작하세요.

| 구분 | Microsoft Foundry | Microsoft Agent Framework |
|------|-------------------|---------------------------|
| **한 줄 정의** | AI 앱·에이전트를 **만들고 배포·운영·거버넌스**하는 클라우드 플랫폼 | 코드로 **에이전트와 워크플로우를 빌드**하는 오픈소스 SDK |
| **형태** | Azure 클라우드 서비스 + 포털([ai.azure.com](https://ai.azure.com)) | Python / .NET 라이브러리 (`pip install agent-framework`) |
| **주로 하는 일** | 모델 배포, 에이전트 호스팅, 관측(observability), 평가, 보안·거버넌스 | 에이전트 정의, 도구 호출, 멀티턴 대화, 멀티 에이전트 오케스트레이션 |
| **비유** | 에이전트가 **살아가는 도시(인프라)** | 에이전트를 **조립하는 공구 세트(코드)** |

> 💡 **핵심**: Agent Framework로 만든 에이전트는 결국 Foundry에 배포된 모델을 호출하고, Foundry 위에서 호스팅·운영될 수 있습니다. 둘은 경쟁 관계가 아니라 **한 팀**입니다.

---

## 📚 목차 & 시간 배분 (약 2.5시간)

| 모듈 | 내용 | 예상 시간 |
|------|------|:--------:|
| [00. 환경 준비](labs/00-setup.md) | Azure 구독 확인, Python·CLI 설치, `az login`, 개념 소개 | 15분 |
| [01. Foundry 포털](labs/01-foundry-portal.md) | 프로젝트 생성 + 모델 배포 (GUI) | 20분 |
| [02. Foundry SDK 기초](labs/02-foundry-sdk.md) | SDK로 모델 직접 호출 (SDK 예제는 이것 하나) | 15분 |
| [03. 첫 에이전트](labs/03-agent-framework-first.md) | MAF 에이전트 만들기 + 로컬/서버 실행 | 20분 |
| [04. 도구 추가](labs/04-agent-framework-tools.md) | 함수 도구 붙이기 + 로컬/서버 실행 | 20분 |
| [05. 워크플로우](labs/05-agent-framework-workflow.md) | 에이전트를 워크플로우로 연결 → 단일 에이전트화 | 20분 |
| [06. Foundry에 배포](labs/06-deploy-hosted-agent.md) | 에이전트·워크플로우를 hosted agent로 배포·호출 | 30분 |
| — | Q&A / 마무리 | 5분 |
| [부록. Copilot CLI](labs/appendix-copilot-cli.md) | GitHub Copilot CLI 실습 *(Optional)* | 15분 |

---

## ✅ 사전 준비 체크리스트

워크샵 시작 전 아래 항목을 미리 준비해 주세요. 자세한 설치 방법은 [00. 환경 준비](labs/00-setup.md)에 있습니다.

- [ ] **Azure 구독** — 유효한 결제가 연결된 구독, Foundry 리소스를 만들 권한(Owner 또는 Contributor)
- [ ] **Python 3.10 이상** — `python --version`으로 확인
- [ ] **Azure CLI** — `az --version`으로 확인 ([설치 가이드](https://learn.microsoft.com/cli/azure/install-azure-cli))
- [ ] **코드 에디터** — Visual Studio Code 권장 (+ Python 확장)
- [ ] **Git** *(선택)* — 이 저장소를 클론하려면 필요

---

## 🚀 빠른 시작

```bash
# 1. 이 저장소를 받은 뒤 code 디렉토리로 이동
cd code

# 2. 가상환경 생성 & 활성화 (권장)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. Azure 로그인
az login

# 5. 환경변수 설정 (.env.example를 복사해서 값 채우기)
cp ../.env.example ../.env
```

이후 각 랩 문서의 순서대로 따라가면 됩니다.

---

## 📁 저장소 구조

```
.
├── README.md                          # 지금 보고 있는 문서
├── .env.example                       # 환경변수 템플릿
├── labs/                              # 실습 가이드 (한국어)
│   ├── 00-setup.md
│   ├── 01-foundry-portal.md
│   ├── 02-foundry-sdk.md
│   ├── 03-agent-framework-first.md
│   ├── 04-agent-framework-tools.md
│   ├── 05-agent-framework-workflow.md
│   ├── 06-deploy-hosted-agent.md
│   └── appendix-copilot-cli.md
└── code/                              # 복붙 가능한 실습 코드
    ├── requirements.txt               # 로컬 개발용 의존성
    ├── 01_chat_model.py               # Lab 02: Foundry SDK 기초 (유일한 SDK 예제)
    ├── maf_basic/                     # Lab 03: MAF 기본 에이전트
    │   ├── main.py                    #   local | serve | call 모드
    │   ├── agent.yaml                 #   hosted agent 컨테이너 설정
    │   ├── agent.manifest.yaml        #   배포 매니페스트
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── .env.example
    ├── maf_tools/                     # Lab 04: 함수 도구 에이전트 (동일 구조)
    └── maf_workflow/                  # Lab 05: 워크플로우 → 단일 에이전트 (동일 구조)
```

---

## 📎 참고 링크

- [Microsoft Foundry 문서](https://learn.microsoft.com/azure/ai-foundry/)
- [Microsoft Agent Framework 문서](https://learn.microsoft.com/agent-framework/)
- [Agent Framework GitHub (샘플 포함)](https://github.com/microsoft/agent-framework)
- [Foundry 포털](https://ai.azure.com)

---

> 이 자료는 워크샵 진행을 위해 제작되었습니다. API는 빠르게 변할 수 있으니, 문제가 생기면 위 공식 문서를 함께 확인하세요.
