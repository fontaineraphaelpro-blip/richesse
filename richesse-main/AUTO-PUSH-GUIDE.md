# Auto-Push Helper Scripts

Utilisation rapide pour automatiser git add/commit/push après chaque modification.

## Option 1: Script PowerShell (Windows)
```powershell
./auto-push.ps1 -Message "🎨 Update scanner filters"
```

## Option 2: Script Bash (Linux/Mac/WSL)
```bash
./git-push.sh "🎨 Update scanner filters"
```

## Option 3: Alias Git (tous les OS)
```bash
git config --global alias.quickpush '!git add . && git commit -m'
git quickpush "🎨 Update scanner filters"
```

## Shortcut PowerShell
Ajouter à votre profil PowerShell:
```powershell
function gpush {
    param([string]$msg)
    git add .
    git commit -m $msg
    git push origin main
}
```

Usage: `gpush "🎨 Update scanner filters"`
