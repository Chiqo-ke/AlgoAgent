# Old Documentation Archive List

**Date:** December 3, 2025  
**Purpose:** List of documentation that can be archived (now consolidated into new docs)

---

## Why Archive?

The following files contained valuable information that has been **consolidated into 5 new master documents:**
- ✅ ARCHITECTURE.md (1,400 lines)
- ✅ STATUS.md (800 lines)
- ✅ SETUP_AND_INTEGRATION.md (900 lines)
- ✅ QUICK_REFERENCE.md (600 lines)
- ✅ DOCUMENTATION_INDEX.md (600 lines)

Keeping all old files creates duplicate information and confusion. Solution: Archive them to `_legacy_docs/` folder.

---

## Recommendation

### Action Items

1. **Create archive folder:**
   ```bash
   mkdir _legacy_docs
   ```

2. **Move old docs to archive:**
   ```bash
   # Use file explorer or command:
   move [old_file].md _legacy_docs/
   ```

3. **Keep the 5 new docs at root level:**
   - ARCHITECTURE.md
   - STATUS.md
   - SETUP_AND_INTEGRATION.md
   - QUICK_REFERENCE.md
   - DOCUMENTATION_INDEX.md
   - CLEANUP_SUMMARY.md (this summary)

4. **Optional: Create _legacy_docs/README.md:**
   ```markdown
   # Legacy Documentation Archive
   
   These files have been consolidated into the new documentation system.
   See parent directory for current documentation.
   
   - ARCHITECTURE.md (current - replaces all legacy architecture docs)
   - STATUS.md (current - replaces SYSTEM_TEST_REPORT.md, TEST_SUMMARY.md)
   - SETUP_AND_INTEGRATION.md (current - replaces setup guides)
   - QUICK_REFERENCE.md (current - replaces quick start guides)
   - DOCUMENTATION_INDEX.md (current - central navigation hub)
   ```

---

## Files to Archive

### Setup & Installation (6 files)
These are now consolidated in **SETUP_AND_INTEGRATION.md**:
- [ ] INSTALLATION.md
- [ ] SETUP_COMPLETE.md
- [ ] SETUP_AI_API.md
- [ ] QUICK_START_AUTH.md
- [ ] QUICK_START_AI_API.md
- [ ] QUICKSTART_CONVERSATION_MEMORY.md

### Test & Validation Reports (5 files)
These are now consolidated in **STATUS.md**:
- [ ] TEST_SUMMARY.md
- [ ] SYSTEM_TEST_REPORT.md
- [ ] BACKTESTING_PY_MIGRATION_COMPLETE.md
- [ ] API_INTEGRATION_COMPLETE.md
- [ ] API_INTEGRATION_SUMMARY.md

### Architecture & Design (4 files)
These are now consolidated in **ARCHITECTURE.md**:
- [ ] STRATEGY_TEMPLATE_WORKFLOW.md
- [ ] TEMPLATE_WORKFLOW_GUIDE.md
- [ ] TEMPLATE_MIGRATION_STEPS.md
- [ ] TEMPLATE_FEATURE_SUMMARY.md

### Feature Implementation Docs (8 files)
These are now covered in **ARCHITECTURE.md** → Relevant Sections:
- [ ] CONVERSATION_MEMORY_INTEGRATION.md (Section C.6)
- [ ] CONVERSATION_MEMORY_QUICKSTART.md (Section D)
- [ ] CONVERSATION_MEMORY_SETUP.md (Section I)
- [ ] CONVERSATION_MEMORY_SUMMARY.md (Section C.6)
- [ ] CONVERSATION_MEMORY_WITH_VALIDATION.md (Section C.6)
- [ ] DATA_LOADER_UPGRADE.md (Section C.5)
- [ ] INDICATOR_FIX_SUMMARY.md (Section C.3)
- [ ] STRATEGY_CODE_GENERATION_IMPLEMENTATION.md (Section C.3)

### Integration & API Docs (4 files)
These are now consolidated in **SETUP_AND_INTEGRATION.md** → API Integration:
- [ ] STRATEGY_AI_INTEGRATION_SUMMARY.md
- [ ] JWT_AUTH_IMPLEMENTATION_SUMMARY.md
- [ ] INTEGRATION_COMPLETE.md (Gemini integration - now in Section C.5)
- [ ] STRATEGY_IMPORT_FIX.md

### Troubleshooting & Fixes (7 files)
These are now in **STATUS.md** → Troubleshooting:
- [ ] STRATEGY_FIXES_INDEX.md
- [ ] STRATEGY_FIXES_README.md
- [ ] STRATEGY_FIXES_SUMMARY.md
- [ ] STRATEGY_QUICK_FIX.md
- [ ] STRATEGY_CREATION_TROUBLESHOOTING.md (from root)
- [ ] WEBSOCKET_FIX_SUMMARY.md
- [ ] VALIDATION_WORKFLOW.md

### Quick Start Guides (4 files)
These are now in **QUICK_REFERENCE.md**:
- [ ] STRATEGY_QUICKSTART.md (Strategy/ folder)
- [ ] Backtest/QUICK_REFERENCE.md
- [ ] Backtest/QUICK_START.md
- [ ] Backtest/QUICK_START_COMMANDS.md

### System Prompt & AI Docs (3 files)
These are now in **ARCHITECTURE.md** Section C.5:
- [ ] SYSTEM_PROMPT_UPDATE_SUMMARY.md
- [ ] AI_STRATEGY_API_GUIDE.md
- [ ] AI_FORMATTING_FREEDOM.md

### Production & Deployment (3 files)
These are now in **SETUP_AND_INTEGRATION.md** → Production Deployment:
- [ ] PRODUCTION_API_GUIDE.md (Keep - detailed API reference)
- [ ] REALTIME_BACKTEST_VISUALIZATION.md
- [ ] WEBSOCKET_FIX_SUMMARY.md

### Other (6 files)
These are now elsewhere:
- [ ] BACKTESTING_TEMPLATE_USAGE.md (Backtest/ folder - covered in QUICK_REFERENCE)
- [ ] COMPLETION_REPORT.md (root - status update)
- [ ] EXACT_CODE_CHANGES.md (root - change history)
- [ ] IMPLEMENTATION_COMPLETE.md (root - status update)
- [ ] SESSION_WORK_SUMMARY.md (root - session notes)
- [ ] VISUAL_SUMMARY.md (root - visual guide)

---

## Files to KEEP (Don't Archive)

### Master Documentation (Keep at root level)
- ✅ **ARCHITECTURE.md** - System design specification
- ✅ **STATUS.md** - Component health & current state
- ✅ **SETUP_AND_INTEGRATION.md** - Installation & deployment
- ✅ **QUICK_REFERENCE.md** - Developer quick reference
- ✅ **DOCUMENTATION_INDEX.md** - Navigation hub
- ✅ **CLEANUP_SUMMARY.md** - This cleanup overview

### Feature-Specific Docs (Keep if actively maintained)
- ✅ **PRODUCTION_API_GUIDE.md** - Detailed API reference
- ✅ **Backtest/SYSTEM_PROMPT_BACKTESTING_PY.md** - AI system prompt
- ✅ **Strategy/interactive_strategy_tester.py** - CLI tool code

### Configuration Files (Keep)
- ✅ **.env** - Environment variables
- ✅ **requirements.txt** - Python dependencies
- ✅ **pytest.ini** - Test configuration
- ✅ **manage.py** - Django management
- ✅ **start_server.ps1** - Server launcher

### Code Files (Keep all - no changes)
- ✅ All `.py` files in apps/
- ✅ All test files in `tests/`
- ✅ All strategy generation code
- ✅ All adapter code

---

## Archive Instructions

### Method 1: Using File Explorer
1. Create folder: `_legacy_docs`
2. Select files from "Files to Archive" list above
3. Move them to `_legacy_docs/`
4. Verify 5 main docs are at root level

### Method 2: Using PowerShell
```powershell
# Create archive folder
New-Item -ItemType Directory -Path "_legacy_docs" -ErrorAction SilentlyContinue

# Move old files (adjust paths as needed)
Move-Item -Path "INSTALLATION.md" -Destination "_legacy_docs/"
Move-Item -Path "SETUP_COMPLETE.md" -Destination "_legacy_docs/"
Move-Item -Path "TEST_SUMMARY.md" -Destination "_legacy_docs/"
# ... repeat for each file

# Verify new structure
Get-ChildItem -Filter "*.md" | Select-Object Name
```

### Method 3: Create Archive Listing
```bash
# Create a listing of what was archived
ls _legacy_docs/ > ARCHIVED_FILES.txt
```

---

## Post-Archive Cleanup

### Update README.md
Add to top of README.md:
```markdown
## 📚 Documentation

See **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** to navigate all documentation.

**Quick Links:**
- [Architecture](ARCHITECTURE.md) - System design
- [Status](STATUS.md) - Component health  
- [Setup Guide](SETUP_AND_INTEGRATION.md) - Installation
- [Quick Ref](QUICK_REFERENCE.md) - Commands & API
```

### Create .gitignore Entry
```bash
# Keep legacy docs out of version control (optional)
_legacy_docs/
```

### Update CI/CD (if applicable)
- No changes needed - only moved documentation
- All code files unchanged
- All test files unchanged

---

## Benefits of Archiving

✅ **Reduced Clutter** - 50+ files → 5 main files
✅ **Clearer Navigation** - Users know where to look
✅ **Single Source of Truth** - Less duplicate information
✅ **Easier Maintenance** - Update one doc instead of many
✅ **Preserved History** - Old docs still available if needed
✅ **Professional** - Clean directory structure

---

## What Gets Archived Summary

```
Current: 50+ markdown files scattered
After:   5 consolidated master docs + _legacy_docs/ archive

Root level (tidy):
├── ARCHITECTURE.md                  ← Master arch doc
├── STATUS.md                        ← Master status doc
├── SETUP_AND_INTEGRATION.md        ← Master setup doc
├── QUICK_REFERENCE.md              ← Master quick ref
├── DOCUMENTATION_INDEX.md           ← Navigation hub
├── CLEANUP_SUMMARY.md              ← This summary
├── PRODUCTION_API_GUIDE.md         ← Keep (detailed API ref)
├── README.md                        ← Update with links
├── requirements.txt
├── manage.py
├── db.sqlite3
├── ... (all code files)
│
└── _legacy_docs/
    ├── INSTALLATION.md
    ├── SETUP_COMPLETE.md
    ├── TEST_SUMMARY.md
    ├── ... (45+ old files)
    └── README.md (describing archive)
```

---

## Timeline

**Immediate (Today):**
- ✅ Create 5 new master docs
- ✅ Create this archive list
- ✅ Archive old files (optional)

**This Week:**
- Update README.md with new structure
- Update team wiki/docs with new links
- Notify team of changes

**Going Forward:**
- Maintain 5 master docs
- Archive new legacy docs when consolidated
- Review quarterly for updates

---

## Checklist

- [ ] Read DOCUMENTATION_INDEX.md
- [ ] Review ARCHITECTURE.md
- [ ] Review STATUS.md
- [ ] Create `_legacy_docs/` folder
- [ ] Move old files to archive (or delete if confident)
- [ ] Update README.md
- [ ] Notify team of changes
- [ ] Update any external links
- [ ] Celebrate cleaner documentation! 🎉

---

## Questions?

**What if I need an old document?**
→ Check `_legacy_docs/` folder - everything is preserved

**Can I delete old files instead of archiving?**
→ Yes, but archiving is safer - gives time to verify nothing was missed

**Should I commit this to git?**
→ Yes - commit the 5 new docs and archive folder
→ Use .gitignore if you want to exclude `_legacy_docs/`

**How do I find information from old docs?**
→ Use DOCUMENTATION_INDEX.md → "Documentation by Task"
→ Or search within the 5 consolidated docs

---

**END OF ARCHIVE LIST**

**Ready to clean up?** Start with the Checklist above!
