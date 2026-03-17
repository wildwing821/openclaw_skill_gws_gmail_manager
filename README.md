# GWS Gmail Manager Plugin

Empower your AI Agent to become a professional purifier of digital mailboxes. This tool provides a strongly-typed, high-performance, and token-efficient interface for automated Gmail maintenance.

## Why GWS Gmail Manager?

In the realm of AI automation, bloated email bodies often lead to massive token consumption and context overflow. This plugin is built on the **First Principle** of "Communication Purity" [cite: 2026-01-16, 2026-02-14]. By utilizing **Pydantic** for rigorous data validation and implementing smart parsing mechanisms, it ensures that your Agent receives only the most refined and decoded information.

## Skill Marketplace

The plugin offers three core skill modes to elegantly govern your email flow:

| Skill Mode | Core Capability | Key Arguments |
| :--- | :--- | :--- |
| **list** | Performs an enriched search that concurrently fetches subjects and senders to reduce redundant calls. | `--query`, `--limit` |
| **read** | Supports batch reading with smart truncation to prevent token explosion. | `--message_ids`, `--full_body` |
| **manage** | Executes batch classification, archiving, trashing, or permanent purification. | `--action_type`, `--target_label` |

## Getting Started

### Prerequisites
1.  **Core Dependency**: Ensure `@googleworkspace/cli (gws)` is installed and executable in your system.
2.  **Authentication**: OAuth 2.0 authentication must be completed with credentials placed in the config directory.
3.  **Defensive Initialization**: All file outputs must strictly follow the **Path Dependency Trap** review; ensure parent directories are created via `mkdir -p` before redirection [cite: 2026-02-26].

### Configuration
Set the required environment variable to point to your credentials:
```bash
# Must point to the directory containing your gws configuration
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="/app/.openclaw/config/gws"
```

## Project Structure

This plugin adheres to a strict layered architecture to maintain logic purity and stability [cite: 2026-02-07]:

```text
gws-gmail-manager/
├── gws_gmail_manager.py     # Business Logic & Entry Point (Strictly Typed) [cite: 2026-02-07]
├── SKILL.md                 # Instruction set for AI Agents
└── README.md                # Project Overview & Manual
```

## Core Engineering Philosophy

### 1. Extreme Token Efficiency
* **Enriched List**: Synchronously retrieves metadata during the listing phase, eliminating unnecessary round-trips for basic information.
* **Smart Truncation**: Automatically prunes email bodies (defaulting to the first 150 characters) to balance information density with transmission costs.

### 2. Pure Technical Contracts
* **Type Safety**: Leverages **Pydantic** for domain models, ensuring data integrity and the automatic cleansing of `None` values or redundant whitespaces.
* **Async Performance**: Implements `asyncio.Semaphore` to throttle API requests, balancing speed with system stability [cite: 2026-02-07].

### 3. Defensive & State-less Principles
* **Path Guarding**: Strictly rejects default path assumptions; all outputs are guarded by directory existence checks [cite: 2026-02-26].
* **Action Safty**: using `trash` (safe/recoverable) instead of  `delete` (permanent purification) to ensure operational safety.



讓 AI Agent 成為數位信箱的專業淨化使者。本工具專為追求極致效率的開發者設計，將複雜的 Gmail 管理轉化為強型別、高安全性且 Token 友善的自動化流程。

## 為什麼選擇 GWS Gmail Manager

在自動化信箱管理的過程中，冗長的郵件正文常導致 LLM Token 爆量。本插件核心圍繞「通訊純淨度」設計，透過 Pydantic 強型別驗證與智慧解析機制，確保 Agent 僅接收最精煉、且經過解碼的有效資訊。

## 技能矩陣 (Skill Marketplace)

本插件提供三種核心技能模式，協助您優雅地控制郵件流：

| 技能模式 | 核心功能 | 關鍵參數 |
| :--- | :--- | :--- |
| **list** | 執行富郵件清單檢索，內建主旨與寄件者併發獲取機制。 | `--query`, `--limit` |
| **read** | 支援多 ID 批次讀取，預設執行智慧截斷以防止 Token 溢出。 | `--message_ids`, `--full_body` |
| **manage** | 批次執行分類、歸檔、垃圾桶移入或永久淨化動作。 | `--action_type`, `--target_label` |

## 快速上手 (Getting Started)

### 環境要求
1.  **底層依賴**：確保環境中已安裝 `@googleworkspace/cli (gws)` 執行檔。
2.  **認證授權**：需完成 OAuth 2.0 認證流程，並取得憑證。
3.  **路徑配置**：所有日誌或輸出若需導向檔案，請遵循防禦性原則，先行建立父目錄。

### 配置環境變數
```bash
# 指向包含認證憑證的配置目錄
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="/app/.openclaw/config/gws"
```


## 專案結構 (How it Works)

本插件遵循嚴謹的工程分層架構，確保邏輯的純粹與穩定性：

```text
gws-gmail-manager/
├── gws_gmail_manager.py     # 核心業務邏輯與 Entry Point
├── SKILL.md                 # 針對 AI Agent 的指令規範
└── README.md                # 專案概覽與使用手冊
```

## 核心設計哲學

### 1. 極致 Token 優化 (Token Efficiency)
* **Enriched List**: 檢索階段即同步抓取主旨與寄件者，消除重複呼叫 read 的無謂消耗。
* **Smart Truncation**: 讀取郵件時預設僅取前 150 字，在資訊獲取與傳輸成本間取得完美平衡。

### 2. 強型別契約 (Type Safety)
* 採用 **Pydantic** 定義領域模型，並具備 Base64url 自動解碼機制，確保 Agent 接收的是純淨無汙垢的資料。

### 3. 防禦性批次操作 (Safe Operations)
* **併發控制**：支援多 ID 批次處理，提升處理效率的同時維持系統穩定。
* **安全動作**：用 `trash`（安全還原）替代 `delete`（永久淨化）動作，確保操作安全性。
