# skills/ — how Jarvis gets better over time

This is the lightweight, safe alternative to a "self-evolving agent" framework.

**The loop:**
1. When Jarvis nails a non-trivial task, it writes a short playbook here as
   `some-task.md` (steps, which tools, gotchas).
2. The system prompt tells Jarvis to check this folder before similar tasks.
3. The nightly `briefing.py` run includes a reflection step that proposes new or
   improved skills based on what happened that day.

Each skill is just Markdown:

```markdown
# Skill: file my morning expenses
When: I say "do my expenses"
Tools: composio (gmail search), desktop-commander (save receipts), approval gate on send
Steps:
1. Search inbox for receipts since yesterday 6pm
2. Save attachments to D:\receipts\YYYY-MM
3. Draft the Expensify entries — DO NOT submit; wait for my OK
Gotchas: skip anything already tagged "filed"
```

Keep them small and specific. Over weeks this becomes Jarvis's institutional
memory of *how you like things done* — most of the benefit of "self-improving"
with none of the runaway risk.
