# MQL5 Documentation Guide

**Quick reference for choosing the right document**

---

## 📚 Two Complementary Documents

### 1. **MQL5_SETUP_GUIDE.md** - For Human Users 👤
**Purpose:** Step-by-step instructions for setting up and running MT5 integration

**Use this when:**
- You want to test your Python strategy in MT5
- You need to set up the EA for the first time
- You're troubleshooting MT5 issues
- You want to understand the complete workflow

**Structure:**
- Prerequisites and requirements
- 7 detailed setup steps
- File locations and paths
- Configuration screenshots/examples
- Troubleshooting common issues
- Complete working examples
- Checklists for validation

**Target Audience:** Traders, developers, users implementing MT5 validation

---

### 2. **MQL5_CODE_SPECIFICATION.md** - For AI Models 🤖
**Purpose:** Technical specification for generating MQL5 code compatible with Python module

**Use this when:**
- You want AI to generate MQL5 Expert Advisor code
- You need to understand the data format specifications
- You're developing custom MT5 solutions
- You want to ensure compatibility with Python backtest

**Structure:**
- Input data format (CSV specification)
- Required MQL5 components (functions, structures)
- Signal execution logic (detailed algorithms)
- Python interface specifications
- Validation requirements
- Error handling rules
- Success criteria

**Target Audience:** AI models, developers creating custom MQL5 EAs, technical architects

---

## 🎯 Quick Decision Matrix

| Your Goal | Use This Document |
|-----------|-------------------|
| "I want to validate my strategy in MT5" | **MQL5_SETUP_GUIDE.md** |
| "Generate MQL5 code that works with my Python code" | **MQL5_CODE_SPECIFICATION.md** |
| "Where do I copy the EA file?" | **MQL5_SETUP_GUIDE.md** |
| "What CSV format does Python export?" | **MQL5_CODE_SPECIFICATION.md** |
| "MT5 won't load my signal file" | **MQL5_SETUP_GUIDE.md** (Troubleshooting) |
| "How should the EA parse timestamps?" | **MQL5_CODE_SPECIFICATION.md** |
| "What settings should I use in Strategy Tester?" | **MQL5_SETUP_GUIDE.md** |
| "What signal types must the EA handle?" | **MQL5_CODE_SPECIFICATION.md** |
| "How do I compare Python vs MT5 results?" | **MQL5_SETUP_GUIDE.md** (Step 7) |
| "What data structures are required in MQL5?" | **MQL5_CODE_SPECIFICATION.md** |

---

## 📖 Recommended Reading Order

### For First-Time Users:
1. **MQL5_SETUP_GUIDE.md** - Start here
2. Try the example workflow
3. Reference **MQL5_CODE_SPECIFICATION.md** if you need to modify the EA

### For AI Code Generation:
1. **MQL5_CODE_SPECIFICATION.md** - Complete specification
2. Reference **MQL5_SETUP_GUIDE.md** for context about user workflow
3. Use the existing `PythonSignalExecutor.mq5` as implementation reference

### For Developers:
1. **MQL5_CODE_SPECIFICATION.md** - Technical requirements
2. **MQL5_SETUP_GUIDE.md** - User experience requirements
3. **MT5_INTEGRATION_GUIDE.md** - Deep dive into integration architecture

---

## 🔄 How They Work Together

```
Python Backtest
    ↓
SimBroker exports CSV
    ↓
[CSV Format defined in MQL5_CODE_SPECIFICATION.md]
    ↓
User follows MQL5_SETUP_GUIDE.md
    ↓
Copy files, configure EA
    ↓
MT5 EA (built per MQL5_CODE_SPECIFICATION.md)
    ↓
Execution & Results
    ↓
Reconciliation (in MQL5_SETUP_GUIDE.md)
```

---

## 💡 Key Differences

| Aspect | MQL5_SETUP_GUIDE.md | MQL5_CODE_SPECIFICATION.md |
|--------|---------------------|---------------------------|
| **Tone** | Instructional, step-by-step | Technical, specification |
| **Format** | Tutorial with examples | Formal specification |
| **Code Examples** | Complete workflows | Function signatures, logic |
| **Focus** | "How to use" | "How to build" |
| **Audience** | End users | Developers & AI models |
| **Length** | ~800 lines | ~600 lines |
| **Depth** | Practical implementation | Technical requirements |

---

## 🚀 Quick Start Paths

### Path 1: Just Run It (Fastest)
1. Read **MQL5_SETUP_GUIDE.md** → Steps 1-6
2. Use existing `PythonSignalExecutor.mq5`
3. Done! ✅

### Path 2: Modify Existing EA
1. Read **MQL5_CODE_SPECIFICATION.md** → Understand format
2. Modify `PythonSignalExecutor.mq5`
3. Test using **MQL5_SETUP_GUIDE.md**

### Path 3: Generate New EA with AI
1. Give AI model **MQL5_CODE_SPECIFICATION.md**
2. Prompt: "Generate MQL5 EA following this specification"
3. Test using **MQL5_SETUP_GUIDE.md**

### Path 4: Custom Integration
1. Study **MQL5_CODE_SPECIFICATION.md** → All requirements
2. Design your implementation
3. Validate against **MQL5_SETUP_GUIDE.md** → Success criteria

---

## 📋 Documentation Hierarchy

```
MT5 Integration Documentation
│
├── For Quick Start (5 minutes)
│   └── MT5_QUICK_REFERENCE.md
│
├── For Human Setup (Complete)
│   └── MQL5_SETUP_GUIDE.md ← Start here for users
│
├── For Code Generation (AI)
│   └── MQL5_CODE_SPECIFICATION.md ← Start here for AI
│
├── For Deep Understanding
│   └── MT5_INTEGRATION_GUIDE.md (1,200+ lines)
│
└── For Executive Overview
    └── README_MT5_INTEGRATION.md
```

---

## ✅ Which Document Should You Give to an AI Model?

### To Generate MQL5 Code:
**Give:** `MQL5_CODE_SPECIFICATION.md`

**Why:**
- Precise data format specifications
- Function signatures and requirements
- Signal execution logic algorithms
- Validation rules
- Error handling specifications
- Clear success criteria
- Structured for code generation

**Example Prompt:**
```
I have a Python backtesting module that exports signals to CSV.
Generate an MQL5 Expert Advisor following the specification in MQL5_CODE_SPECIFICATION.md.
The EA must read the CSV and execute signals in MT5 Strategy Tester.
```

### To Explain User Workflow:
**Give:** `MQL5_SETUP_GUIDE.md`

**Why:**
- Step-by-step procedures
- User-facing instructions
- Troubleshooting guides
- Configuration examples
- Complete workflows

**Example Prompt:**
```
Explain how a user would validate their Python trading strategy in MetaTrader 5
using the workflow described in MQL5_SETUP_GUIDE.md.
```

---

## 🎯 Summary

- **MQL5_SETUP_GUIDE.md** = "How to USE the system" 👤
- **MQL5_CODE_SPECIFICATION.md** = "How to BUILD the system" 🤖

Both documents describe the same system from different perspectives:
- **Setup Guide** walks users through the process
- **Code Spec** defines what the code must do

Use **Code Spec** for AI generation, **Setup Guide** for human implementation!

---

**Quick Links:**
- [MQL5_SETUP_GUIDE.md](MQL5_SETUP_GUIDE.md) - User guide
- [MQL5_CODE_SPECIFICATION.md](MQL5_CODE_SPECIFICATION.md) - Technical spec
- [PythonSignalExecutor.mq5](PythonSignalExecutor.mq5) - Reference implementation
