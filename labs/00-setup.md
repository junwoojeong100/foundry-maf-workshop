# Lab 00. 환경 준비 & 개념 소개

> ⏱️ 예상 시간: 15분

이 랩에서는 실습에 필요한 도구를 설치하고, Foundry와 Agent Framework의 개념을 정리합니다.

---

## 🎯 목표

- 실습 환경(Python, Azure CLI, 로그인)을 완성한다.
- Microsoft Foundry와 Agent Framework의 차이를 이해한다.

---

## 1. 개념 먼저 잡기

| 질문 | Microsoft Foundry | Microsoft Agent Framework |
|------|-------------------|---------------------------|
| **무엇인가?** | AI 앱·에이전트를 만들고 배포·운영하는 **클라우드 플랫폼** | 에이전트를 코드로 빌드하는 **오픈소스 SDK** |
| **어디서 쓰나?** | 포털([ai.azure.com](https://ai.azure.com)) + Azure 리소스 | 내 코드 (`pip install agent-framework-core`) |
| **무엇을 하나?** | 모델 배포, 에이전트 호스팅, 관측·평가·거버넌스 | 에이전트 정의, 도구 호출, 워크플로우 |

**오늘의 실습 흐름**

```
Lab 01  Foundry 포털에서 모델 배포        ← 플랫폼 준비
Lab 02  Foundry SDK로 모델 직접 호출        ← 플랫폼을 코드로 사용
Lab 03  Agent Framework 첫 에이전트        ← SDK로 에이전트 조립
Lab 04  도구(함수) 붙이기
Lab 05  워크플로우로 연결
Lab 06  Foundry에 hosted agent로 배포      ← 다시 플랫폼으로 (한 바퀴 완성)
```

---

## 2. 사전 요구사항 확인

### 2-1. Python 3.13 이상

```bash
python3 --version
# 예: Python 3.13.5  → OK (3.13 미만이면 업그레이드 필요)
```

> Windows에서 WSL/Git Bash를 쓰지 않는다면 `py -3.13 --version`으로 확인하세요.

### 2-2. Azure CLI

```bash
az --version
```

설치가 안 되어 있다면 [Azure CLI 설치 가이드](https://learn.microsoft.com/cli/azure/install-azure-cli)를 따르세요.

- **macOS**: `brew install azure-cli`
- **Windows**: [MSI 설치 관리자](https://aka.ms/installazurecliwindows)
- **Linux**: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`

### 2-3. Azure 구독 & 권한

- 유효한 **Azure 구독**이 있어야 합니다.
- Foundry 리소스를 만들려면 대상 리소스 그룹에 **Contributor** 이상이 필요합니다.
- Lab 01에서 역할 할당까지 직접 하려면 **Owner** 또는 **Role Based Access Control Administrator**가 추가로 필요합니다.

### 2-4. Bash 호환 터미널

이 가이드의 여러 줄 명령은 Bash 문법을 사용합니다.

- macOS/Linux: 기본 터미널 사용
- Windows: **WSL** 또는 **Git Bash** 권장
- PowerShell만 쓴다면 줄 연속 문자(`\`)와 `cp`, `mkdir -p` 명령을 PowerShell 문법으로 바꿔야 합니다.

---

## 3. 프로젝트 코드 준비

```bash
# 실습 코드 디렉토리로 이동
cd code

# 가상환경 생성 & 활성화 (권장)
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux/WSL/Git Bash
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 의존성 설치
python -m pip install -r requirements.txt
```

설치되는 주요 패키지:

- `azure-ai-projects==2.3.0` — Foundry SDK (Lab 02 기초 예제)
- `agent-framework-core` — Agent Framework 코어 (Lab 03~06)
- `agent-framework-foundry` — Foundry 전용 클라이언트 `FoundryChatClient`/`FoundryAgent`
- `agent-framework-foundry-hosting` — hosted agent를 로컬에서 serve (Lab 03~06)
- `azure-identity` — 인증
- `python-dotenv` — `.env` 파일 로딩

> 💡 Lab 06의 **배포**는 Azure Developer CLI(`azd`)로 합니다. 설치는 Lab 06에서 안내합니다.
>
> `agent-framework` 메타 패키지는 모든 선택 기능을 함께 설치합니다. 이 워크샵은 Foundry에 필요한 `agent-framework-core`와 전용 패키지만 설치해 로컬 환경과 Linux 원격 빌드의 의존성을 동일하게 유지합니다.

---

## 4. Azure 로그인

```bash
az login
```

브라우저가 열리면 계정으로 로그인합니다. 여러 구독이 있다면 사용할 구독을 지정하세요.

```bash
# 구독 목록 보기
az account list --output table

# 사용할 구독 선택
az account set --subscription "<구독 ID 또는 이름>"
```

> 💡 이 실습의 코드는 `DefaultAzureCredential`을 사용합니다.
> 즉, `az login`으로 로그인해두면 코드에 키를 하드코딩할 필요가 없습니다.

---

## 5. 환경변수 템플릿 준비

아직 Foundry 프로젝트를 만들지 않았으므로 값은 [Lab 01](01-foundry-portal.md)에서 채웁니다. 지금은 템플릿만 복사해 둡니다.

```bash
# 현재 위치가 code/이므로 저장소 루트에 생성
cp ../.env.example ../.env
```

`.env` 파일 내용:

```bash
FOUNDRY_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4
FOUNDRY_AGENT_NAME=maf-basic-agent
```

> 💡 환경변수 이름은 Foundry hosting 인프라가 요구하는 `FOUNDRY_PROJECT_ENDPOINT` / `AZURE_AI_MODEL_DEPLOYMENT_NAME`으로 통일했습니다. 배포(azd) 후에는 이 두 값을 인프라가 자동 주입합니다.

---

## ✅ 체크포인트

- [ ] `python3 --version` → 3.13 이상
- [ ] `az --version` → 정상 출력
- [ ] `python -m pip install -r requirements.txt` → 오류 없이 완료
- [ ] `az login` → 로그인 성공
- [ ] `.env` 파일 생성 완료 (값은 다음 랩에서 채움)

모두 체크했다면 👉 **[Lab 01. Foundry 포털](01-foundry-portal.md)** 로 이동하세요.
