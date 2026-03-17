import asyncio
import json
import logging
import argparse
import sys
import os
import base64
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# ==========================================
# 0. Infrastructure & Configuration Layer
# ==========================================
class Settings:
    """
    Centralized environment and path management.
    Implements the Single Source of Truth (SSOT) principle.
    """
    PROJECT_ROOT: Path = Path("/app/.openclaw")
    # Defensive Path: GOOGLE_WORKSPACE_CLI_CONFIG_DIR must be ensured before usage [cite: 2026-02-26]
    GWS_CONFIG_DIR: Path = PROJECT_ROOT / "config" / "gws"
    
    # Token Optimization Defaults
    DEFAULT_BODY_TRUNCATE_LEN: int = 150
    MAX_CONCURRENT_TASKS: int = 10  # Throttles API calls to protect subprocesses and rate limits

settings = Settings()

# Standardized logging using stderr to keep stdout pure for JSON output [cite: 2026-02-07, 2026-02-26]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("yggdrasil.gmail")

# ==========================================
# 1. Domain Model Layer
# ==========================================
class GmailMessage(BaseModel):
    """
    Strongly-typed data contract serving as the interface for the LLM.
    Ensures data purity and consistency.
    """
    id: str = Field(..., description="Unique message identifier")
    threadId: Optional[str] = Field(None, description="Conversation thread identifier")
    subject: Optional[str] = Field(None, description="Email subject line")
    sender: Optional[str] = Field(None, description="Sender information (From)")
    date: Optional[str] = Field(None, description="Message date")
    snippet: Optional[str] = Field(None, description="Brief snippet of the message content")
    body: Optional[str] = Field(None, description="Plain text body content")
    
    def dump_for_llm(self) -> Dict[str, Any]:
        """
        Defensive Output: Filters None values and unset fields to minimize Token consumption.
        """
        return self.model_dump(exclude_none=True, exclude_unset=True)

# ==========================================
# 2. Infrastructure Layer
# ==========================================
class GwsCliClient:
    """
    Encapsulates Google Workspace CLI (gws) interactions.
    Decouples external system dependencies from business logic.
    """
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        if not shutil.which("gws"):
            raise RuntimeError("The 'gws' command was not found. Please ensure @googleworkspace/cli is installed.")

    async def run_command(self, *cmd_parts: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes a GWS command safely and returns parsed JSON output.
        """
        if not self.config_dir.exists():
             raise FileNotFoundError(f"Configuration directory missing: {self.config_dir}")

        cmd = ["gws"] + list(cmd_parts)
        if params:
            cmd.extend(["--params", json.dumps(params)])
        cmd.extend(["--format", "json"])

        env = os.environ.copy()
        env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(self.config_dir)
        env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring" # Security purification

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            err_str = stderr.decode().strip() or stdout.decode().strip()
            raise RuntimeError(f"GWS API Error: {err_str}")

        return json.loads(stdout.decode()) if stdout else {}

# ==========================================
# 3. Business Logic Layer
# ==========================================
class GmailManager:
    """
    Core logic for Gmail operations, optimized for LLM efficiency.
    """
    def __init__(self, client: GwsCliClient):
        self.client = client
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

    def _decode_base64url(self, data: str) -> str:
        """Decodes base64url encoded strings safely."""
        try:
            if not data: return ""
            data = data.replace("\n", "").replace("\r", "")
            padding = len(data) % 4
            if padding: data += "=" * (4 - padding)
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Base64 decoding failed: {e}")
            return ""

    def _parse_body(self, payload: Dict[str, Any], truncate_len: int = None) -> str:
        """
        Recursively parses email body with Token-protective truncation.
        """
        parts = payload.get("parts", [])
        body_text = ""
        
        # Priority 1: Plain text
        for part in parts:
            if part.get("mimeType") == "text/plain":
                body_text = self._decode_base64url(part.get("body", {}).get("data", ""))
                break
        else:
            # Priority 2: HTML or nested parts
            for part in parts:
                if part.get("mimeType") == "text/html":
                    body_text = self._decode_base64url(part.get("body", {}).get("data", ""))
                    break
                if "parts" in part:
                    res = self._parse_body(part)
                    if res: 
                        body_text = res
                        break
        
        if not body_text:
            body_text = self._decode_base64url(payload.get("body", {}).get("data", ""))
            
        # Optimization: Truncate long bodies to save Tokens
        if truncate_len and len(body_text) > truncate_len:
            body_text = body_text[:truncate_len] + "...[TRUNCATED FOR TOKEN OPTIMIZATION]"
            
        return body_text.strip()

    async def _fetch_metadata_only(self, message_id: str) -> Optional[GmailMessage]:
        """Internal helper: Fetches only essential metadata to avoid heavy payload transfers."""
        async with self._semaphore:
            try:
                params = {"userId": "me", "id": message_id, "format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]}
                data = await self.client.run_command("gmail", "users", "messages", "get", params=params)
                headers = data.get("payload", {}).get("headers", [])
                find_h = lambda name: next((h['value'] for h in headers if h['name'].lower() == name.lower()), None)
                
                return GmailMessage(
                    id=data.get("id"), 
                    snippet=data.get("snippet"),
                    subject=find_h("subject"), 
                    sender=find_h("from"), 
                    date=find_h("date")
                )
            except Exception as e:
                logger.warning(f"Failed to fetch metadata for message {message_id}: {e}")
                return None

    async def list_messages_enriched(self, limit: int = 5, query: Optional[str] = None) -> List[GmailMessage]:
        """
        Enriched List Mode: Concurrently fetches Subjects and Senders.
        Minimizes the need for the Agent to call 'read' subsequently.
        """
        params = {"userId": "me", "maxResults": limit}
        if query: params["q"] = query
        
        list_data = await self.client.run_command("gmail", "users", "messages", "list", params=params)
        raw_messages = list_data.get("messages", [])
        
        if not raw_messages:
            return []

        # Concurrent retrieval (guarded by Semaphore)
        tasks = [self._fetch_metadata_only(msg["id"]) for msg in raw_messages]
        enriched_results = await asyncio.gather(*tasks)
        
        return [msg for msg in enriched_results if msg is not None]

    async def get_message_detail(self, message_id: str, truncate: bool = True) -> GmailMessage:
        """Fetches full message details with optional body truncation."""
        params = {"userId": "me", "id": message_id, "format": "full"}
        data = await self.client.run_command("gmail", "users", "messages", "get", params=params)
        headers = data.get("payload", {}).get("headers", [])
        find_h = lambda name: next((h['value'] for h in headers if h['name'].lower() == name.lower()), None)
        
        truncate_len = settings.DEFAULT_BODY_TRUNCATE_LEN if truncate else None
        
        return GmailMessage(
            id=data.get("id"), threadId=data.get("threadId"), snippet=data.get("snippet"),
            subject=find_h("subject"), sender=find_h("from"), date=find_h("date"),
            body=self._parse_body(data.get("payload", {}), truncate_len=truncate_len)
        )

    async def batch_manage_action(self, action_type: str, message_ids: List[str], target_label: Optional[str] = None) -> Dict[str, Any]:
        """
        Batch Management: Allows the Agent to process multiple IDs in a single tool call.
        """
        async def _single_action(msg_id: str):
            async with self._semaphore:
                try:
                    if action_type == "trash":
                        await self.client.run_command("gmail", "users", "messages", "trash", params={"userId": "me", "id": msg_id})
                    elif action_type == "delete":
                        # Permanent deletion (dangerous)
                        await self.client.run_command("gmail", "users", "messages", "trash", params={"userId": "me", "id": msg_id})
                    elif action_type == "move" and target_label:
                        await self.client.run_command("gmail", "users", "messages", "modify", params={"userId": "me", "id": msg_id, "addLabelIds": [target_label], "removeLabelIds": ["INBOX"]})
                    return msg_id, "success", None
                except Exception as e:
                    return msg_id, "error", str(e)

        results = await asyncio.gather(*[_single_action(mid) for mid in message_ids])
        
        success_ids = [res[0] for res in results if res[1] == "success"]
        failed_ids = {res[0]: res[2] for res in results if res[1] == "error"}
        
        return {
            "action": action_type,
            "processed_count": len(message_ids),
            "success_count": len(success_ids),
            "failed": failed_ids if failed_ids else None
        }

# ==========================================
# 4. Entry Point & Output Formatting
# ==========================================
def output_json(status: str, data: Any = None, message: str = None):
    """
    Standardizes output format and minifies JSON to save Tokens.
    """
    out = {"status": status}
    if data is not None: out["data"] = data
    if message is not None: out["message"] = message
    # Minimal separators to strip whitespace
    print(json.dumps(out, ensure_ascii=False, separators=(',', ':'))) 

async def main():
    parser = argparse.ArgumentParser(description="Yggdrasil Gmail Agent Tool (Optimized for LLMs)")
    parser.add_argument("skill", choices=["list", "manage", "read"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--query", type=str)
    # Supports comma-separated IDs for batch processing
    parser.add_argument("--message_ids", type=str, help="Single or comma-separated message IDs") 
    parser.add_argument("--action_type", choices=["trash", "delete", "move"])
    parser.add_argument("--target_label", type=str)
    parser.add_argument("--full_body", action="store_true", help="Force read the full body without truncation")

    args = parser.parse_args()
    
    # Dependency Injection
    client = GwsCliClient(config_dir=settings.GWS_CONFIG_DIR)
    manager = GmailManager(client=client)

    try:
        if args.skill == "list":
            # Utilize Enriched List Mode
            res = await manager.list_messages_enriched(limit=args.limit, query=args.query)
            output_json("success", data=[m.dump_for_llm() for m in res])
            
        elif args.skill == "read":
            if not args.message_ids: raise ValueError("--message_ids required for 'read' skill")
            ids = [i.strip() for i in args.message_ids.split(",") if i.strip()]
            
            # Batch read support
            tasks = [manager.get_message_detail(mid, truncate=not args.full_body) for mid in ids]
            res = await asyncio.gather(*tasks)
            output_json("success", data=[m.dump_for_llm() for m in res])
            
        elif args.skill == "manage":
            if not args.message_ids: raise ValueError("--message_ids required for 'manage' skill")
            if not args.action_type: raise ValueError("--action_type required for 'manage' skill")
            ids = [i.strip() for i in args.message_ids.split(",") if i.strip()]
            
            res = await manager.batch_manage_action(args.action_type, ids, args.target_label)
            output_json("success", data=res)
            
    except Exception as e:
        logger.exception("Execution failed")
        output_json("error", message=str(e))

if __name__ == "__main__":
    asyncio.run(main())