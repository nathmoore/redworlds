# AI prompt files

These files are designed to be pasted into an AI conversation (Claude.ai, ChatGPT,
Copilot, or similar) to give the assistant enough context to discuss carbon modelling
with Red Worlds as its scientific backbone.

## How to use

1. Open [red_worlds_context.md](red_worlds_context.md)
2. Copy the full contents
3. Paste it as your first message (or as the system prompt if your tool supports one)
4. Start asking questions — see the example prompts inside the file

## What's here

| File | Purpose |
|------|---------|
| `red_worlds_context.md` | Base context file — start here |

Action-specific prompt files (BUILD, SWAP, REDUCE, compare scenarios) will be added
once those engine functions are implemented and tested. Using them before then would
give the AI incomplete information about how the calculations actually work.

## What these are *not*

These are not scripts or code — they are plain text documents intended to be read by
an AI assistant. They do not run anything; they orient the AI to the project's
assumptions, data structures, and current implementation status so it can give you
accurate, grounded answers.
