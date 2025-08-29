#!/bin/bash
# Setup Git Hooks for Student Success Prediction Platform

echo "🎓 Setting up Git hooks for K-12 Educational Platform..."
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not in a Git repository"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Ensure hooks directory exists
mkdir -p .git/hooks

# Function to install a hook
install_hook() {
    local hook_name="$1"
    local hook_source="$2"
    
    if [ -f "$hook_source" ]; then
        cp "$hook_source" ".git/hooks/$hook_name"
        chmod +x ".git/hooks/$hook_name"
        echo "✅ Installed $hook_name hook"
    else
        echo "⚠️  Warning: $hook_source not found"
    fi
}

# Install hooks if they exist
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hook already installed"
else
    echo "⚠️  Pre-commit hook not found in .git/hooks/"
    echo "   This should have been created automatically"
fi

if [ -f ".git/hooks/pre-push" ]; then
    echo "✅ Pre-push hook already installed"
else
    echo "⚠️  Pre-push hook not found in .git/hooks/"
    echo "   This should have been created automatically"
fi

# Test hooks
echo ""
echo "🧪 Testing Git hooks..."

# Test pre-commit hook
echo "Testing pre-commit hook..."
if [ -x ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hook is executable"
    
    # Quick syntax check
    if bash -n .git/hooks/pre-commit; then
        echo "✅ Pre-commit hook syntax is valid"
    else
        echo "❌ Pre-commit hook has syntax errors"
    fi
else
    echo "❌ Pre-commit hook is not executable"
fi

# Test pre-push hook  
echo "Testing pre-push hook..."
if [ -x ".git/hooks/pre-push" ]; then
    echo "✅ Pre-push hook is executable"
    
    # Quick syntax check
    if bash -n .git/hooks/pre-push; then
        echo "✅ Pre-push hook syntax is valid"
    else
        echo "❌ Pre-push hook has syntax errors"
    fi
else
    echo "❌ Pre-push hook is not executable"
fi

echo ""
echo "🎯 Git Hooks Setup Complete!"
echo ""
echo "What the hooks do:"
echo ""
echo "📋 PRE-COMMIT HOOK:"
echo "   • ✅ FERPA compliance validation (critical)"
echo "   • ✅ Educational content appropriateness (critical)"
echo "   • ✅ GPT Emma Johnson format compliance (critical)"
echo "   • ✅ API authentication & functionality (critical)"
echo "   • ✅ Frontend component validation (critical)"
echo "   • ✅ Database integrity checks (critical)"
echo "   • ⚠️  Code quality checks (warnings)"
echo "   • ⚠️  File size and security scan (warnings)"
echo ""
echo "🚀 PRE-PUSH HOOK:"
echo "   • ✅ Comprehensive security test suite"
echo "   • ✅ Complete GPT AI system validation"
echo "   • ✅ Full frontend test suite"
echo "   • ✅ Database comprehensive validation"
echo "   • ✅ Branch-specific validations"
echo "   • ✅ Sensitive data scanning"
echo "   • ✅ Educational platform compliance"
echo "   • ✅ Performance & resource checks"
echo ""
echo "🔧 USAGE:"
echo "   • Git hooks run automatically during 'git commit' and 'git push'"
echo "   • Critical failures will block commits/pushes"
echo "   • Warnings allow commits but highlight issues"
echo ""
echo "🛠️  TROUBLESHOOTING:"
echo "   • Skip hooks (emergency): git commit --no-verify"
echo "   • Run tests manually:"
echo "     - FERPA: python3 -m pytest tests/api/test_security.py -v"
echo "     - GPT: python3 -m pytest tests/gpt_systems/ -v"
echo "     - Frontend: npm test"
echo "     - Database: python3 -m pytest tests/api/test_database_* -v"
echo ""
echo "🎓 Your K-12 Educational Platform now has automated quality gates!"