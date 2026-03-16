# openclaw_skill_gws_gmail_manager
GWS Gmail Manager: 數位信箱的淨化使者
這是一個 Gmail 管理工具 [cite: 2026-01-16]。透過封裝 Google Workspace CLI (gws)，我們為 AI Agent 提供了一個強型別、高效且節省 Token 的通訊介面，讓自動化信箱管理變得既優雅又安全。

🌸 核心特性
極致 Token 優化：

富清單模式 (Enriched List)：在獲取清單時即併發拉取主旨與寄件者，減少 Agent 重複呼叫 read 的次數。

智慧截斷機制：預設截斷郵件正文（150字），防止長郵件造成 Token 爆量。

防禦性輸出：濾除 JSON 中的 None 值與多餘空格，極大化節省傳輸成本。

嚴謹的工程規範：

強型別契約：使用 Pydantic 定義領域模型，確保資料的一致性與純淨度。

分層架構設計：嚴格區分環境配置、領域模型、基礎設施與業務邏輯層。

併發控制：內建 Semaphore 限制同時執行的 API 請求數量，兼顧效能與系統穩定性。

防禦性啟動原則：遵守「路徑依賴陷阱」審查，所有輸出導向皆經過嚴格的目錄存在檢查 。

🛠 系統要求
底層依賴：需安裝 @googleworkspace/cli (gws)。

認證配置：需完成 OAuth 2.0 認證，並將憑證存放於配置目錄。

環境變數：GOOGLE_WORKSPACE_CLI_CONFIG_DIR 指向認證檔案所在路徑。

🚀 快速上手
本工具支援三種核心模式：

檢索 (list)：
python3 gws_gmail_manager.py list --limit 10 --query "is:unread"

批次讀取 (read)：
python3 gws_gmail_manager.py read --message_ids "ID1,ID2" --full_body

批次管理 (manage)：
python3 gws_gmail_manager.py manage --action_type trash --message_ids "ID1,ID2"

英文版本 (English)
GWS Gmail Manager: 

A Gmail management tool . By encapsulating the Google Workspace CLI (gws), this tool provides AI Agents with a strongly-typed, high-performance, and token-efficient interface for automated mailbox maintenance.

🌸 Key Features
Token Efficiency Excellence:

Enriched List Mode: Concurrently fetches subjects and senders during listing, drastically reducing redundant read calls.

Smart Truncation: Automatically prunes email bodies (default 150 chars) to prevent token overflow.

Defensive Output: Minifies JSON by stripping None values and redundant whitespaces.

Strict Engineering Standards:

Strongly-Typed Contracts: Leverages Pydantic for domain models, ensuring data integrity and purity.

Layered Architecture: Strictly decouples Infrastructure, Domain Models, and Business Logic.

Concurrency Control: Implements asyncio.Semaphore to throttle API requests, balancing speed with system stability.

Defensive Initialization: Adheres to the "Path Dependency Trap" review; all file outputs are guarded by directory existence checks .

🛠 System Requirements
Core Dependency: Requires @googleworkspace/cli (gws) installed in the environment.

Authentication: OAuth 2.0 credentials must be configured and placed in the config directory.

Environment Variable: GOOGLE_WORKSPACE_CLI_CONFIG_DIR must point to the directory containing your gws configuration.

🚀 Usage
The tool operates in three primary skill modes:

Search (list):
python3 gws_gmail_manager.py list --limit 10 --query "is:unread"

Batch Read (read):
python3 gws_gmail_manager.py read --message_ids "ID1,ID2" --full_body

Batch Manage (manage):
python3 gws_gmail_manager.py manage --action_type trash --message_ids "ID1,ID2"
