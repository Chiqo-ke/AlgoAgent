# AlgoAgent - Autonomous Trading Strategy Generator

**Status:** ✅ Production Ready | **Last Updated:** December 3, 2025

## **Overview**
The AI Developer Agent is an **autonomous system** that generates, executes, tests, and automatically fixes trading strategies with zero manual intervention. It combines:
- Natural language → Code generation (Gemini AI with key rotation)
- Automatic bot execution and metric extraction
- Intelligent error detection and classification
- AI-powered iterative error fixing
- Complete result tracking and verification

**Key Achievement:** The agent can now **read execution output, detect errors, and iterate to fix them automatically** using AI.

**Proven:** End-to-end test shows strategy generated → error detected → fixed in 1 iteration → 969 trades executed successfully.

## **Architecture**
**Current**: Autonomous Single Agent with Error Recovery Loop

```
User Request (Natural Language)
        ↓
GeminiStrategyGenerator (with 8-key rotation)
        ↓
Generate Strategy Code
        ↓
BotExecutor (Execute + Capture)
        ↓
   Success? ──YES──→ Return Results (trades, metrics, stats)
        ↓ NO
   BotErrorFixer
        ├─ ErrorAnalyzer (classify 10 error types)
        ├─ AI Fix Generation (Gemini + enhanced context)
        ├─ Write Fixed Code
        └─ Re-execute
                ↓
        Retry Loop (up to max_iterations)
                ↓
        Final Results or Failure Report
```

**No manual intervention required.** The system iterates until success or max attempts reached.
