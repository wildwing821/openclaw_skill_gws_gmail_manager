---
name: gws_gmail_manager
description: Executes Gmail operations via Google Workspace CLI. Supports list retrieval, detailed content reading, and batch message management.
tools:
  - name: gws_gmail_tool
    parameters:
      type: object
      properties:
        skill:
          type: string
          description: |
            The execution mode:
            - 'list': Retrieves an enriched list of latest emails (includes Subject and Sender directly).
            - 'read': Fetches detailed decoded content (includes body, truncated to 150 chars by default).
            - 'manage': Performs batch actions like trash, delete, or move.
        limit:
          type: integer
          description: Maximum number of emails to retrieve. Only valid when skill is 'list'.
        query:
          type: string
          description: Native Gmail search syntax (e.g., 'newer_than:14d'). Only valid when skill is 'list'.
        action_type:
          type: string
          description: Management action to execute (trash, delete, move). Required when skill is 'manage'.
        message_id:
          type: string
          description: Unique identifier (ID) of the target email(s). Supports a single ID or multiple IDs separated by commas (,) for batch processing. Required when skill is 'read' or 'manage'.
        target_label:
          type: string
          description: ID of the target label (e.g., 'IMPORTANT'). Required only when action_type is 'move'.
        full_body:
          type: boolean
          description: Whether to force-read the full body without truncation. Set to true only when deep reading is absolutely necessary.
      required:
        - skill
---
STRICT PROHIBITION: Do not use `web_fetch` to access internal domains or COMPOSIO. Directly invoke the internal Python logic of this skill.

### Default Command (Adopted automatically if not specified)
python3 /app/.openclaw/workspace/skills/gws_gmail_manager/gws_gmail_manager.py list --limit 60 --query 'newer_than:2d'
(Workflow: Scan 2 days of emails -> Identify/Categorize -> Report important emails -> Briefly summarize the rest)

### Recommended SOP (Ad-Cleanup & Token Optimization)
When the user requests mailbox cleanup or unimportance identification, the Agent MUST follow this logic to maximize Token efficiency:
"Use the `list` skill to retrieve emails (Recommended: --query 'newer_than:14d', --limit 60). Since `list` now returns Senders and Subjects directly, analyze and identify newsletters or unimportant emails based solely on these results. Once confirmed, concatenate all target IDs with commas and call `manage --message_ids id1,id2,id3... --action_type trash` once. DO NOT call `read` to fetch the body unless absolutely necessary."

### Command Examples
- **List**: python3 /app/.openclaw/workspace/skills/gws_gmail_manager/gws_gmail_manager.py list --limit 60 --query 'newer_than:2d'
- **Batch Read**: python3 /app/.openclaw/workspace/skills/gws_gmail_manager/gws_gmail_manager.py read --message_ids 18abc123,18xyz456
- **Batch Manage**: python3 /app/.openclaw/workspace/skills/gws_gmail_manager/gws_gmail_manager.py manage --message_ids idA,idB,idC --action_type trash

### Concurrency Principle
When reading or deleting multiple emails, the model SHOULD concatenate multiple `message_ids` using commas (,) within a single tool call. Submit all tasks at once instead of reporting progress message-by-message.

Correct Batching Example: python3 [path] read --message_id A,B,C

### Caching & Final Integration
The model should only write the final summary report after acquiring all necessary email contents. Avoid redundant intermediate dialogues and do not report raw email IDs to the user.