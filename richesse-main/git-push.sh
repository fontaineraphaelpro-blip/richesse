#!/bin/bash
# Auto-push script pour Git
# Usage: ./git-push.sh "Message de commit"

if [ $# -eq 0 ]; then
    echo "❌ Erreur: Fournir un message de commit"
    echo "Usage: ./git-push.sh 'Message de commit'"
    exit 1
fi

MESSAGE="$1"
FILES="${2:-.}"

echo "🔄 Auto-Push Activé"
echo "📝 Message: $MESSAGE"

# 1. Git Add
echo "📦 Stage: git add $FILES"
git add "$FILES"
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du git add"
    exit 1
fi

# 2. Git Commit
echo "💾 Commit..."
git commit -m "$MESSAGE"
if [ $? -eq 1 ]; then
    echo "⚠️ Rien à committer"
    exit 0
fi

# 3. Git Push
echo "🚀 Push vers origin/main..."
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du push"
    exit 1
fi

echo "✅ Push réussi!"
echo "---"
