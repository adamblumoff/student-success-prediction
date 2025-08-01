#!/bin/bash
echo "🧹 Running repository cleanup..."

# Remove Python cache files
echo "  Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove temporary files
echo "  Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name "*_old.py" -delete 2>/dev/null || true
find . -name "*_backup.py" -delete 2>/dev/null || true

# Check for duplicate test files in root
echo "  Checking for duplicate test files..."
if ls test_*.py 1> /dev/null 2>&1; then
    echo "  ⚠️  Found test files in root directory. Consider moving to tests/ directory."
    ls test_*.py
fi

# Check for empty directories (excluding git and venv)
echo "  Checking for empty directories..."
empty_dirs=$(find . -type d -empty | grep -v ".git" | grep -v "venv" | grep -v "__pycache__" || true)
if [ ! -z "$empty_dirs" ]; then
    echo "  ⚠️  Found empty directories:"
    echo "$empty_dirs"
fi

# Show untracked files that might need attention
echo "  Checking git status..."
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | head -5 || true)
if [ ! -z "$untracked" ]; then
    echo "  📋 Untracked files (first 5):"
    echo "$untracked"
fi

echo "✅ Cleanup complete"
echo ""
echo "💡 Next steps:"
echo "  - Review any warnings above"
echo "  - Update DIRECTORY_STRUCTURE.md if structure changed"
echo "  - Update CLAUDE.md with new patterns"
echo "  - Commit changes with descriptive message"