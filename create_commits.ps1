git init
git config core.autocrlf false
git branch -m main

function Commit-File {
    param([string]$path, [string]$msg)
    if (Test-Path $path) {
        git add $path
        git commit -m $msg
    }
}

Commit-File ".gitignore" "Initial commit: Add gitignore template"
Commit-File "README.md" "docs: Add initial project README"
Commit-File "requirements.txt" "chore: Define core dependencies"
Commit-File "src/config.py" "feat: Setup project configuration management"
Commit-File "src/utils" "feat: Implement structured logging utility"
Commit-File "src/fetchers" "feat: Create news fetcher to parse RSS feeds"
Commit-File "src/memory/embeddings.py" "feat: Implement local vector embeddings using sentence-transformers"
Commit-File "src/memory/vector_store.py" "feat: Build ChromaDB vector store for duplicate prevention"
Commit-File "src/agents/curator.py" "feat: Add Curator Agent for AI-driven news selection"
Commit-File "src/agents/writer.py" "feat: Add Writer Agent for drafting dev.to and mastodon posts"
Commit-File "src/agents/graph.py" "feat: Connect agents using LangGraph state machine"
Commit-File "src/publishers/devto.py" "feat: Implement Dev.to API integration for publishing"
Commit-File "src/publishers/mastodon.py" "feat: Implement Mastodon API integration for social broadcast"
Commit-File "main.py" "feat: Create CLI entrypoint for the AI pipeline"
Commit-File ".github" "ci: Setup GitHub Actions cron job for daily execution"
Commit-File "frontend/package.json" "chore: Initialize React Vite frontend project"
Commit-File "frontend/package-lock.json" "chore: Lock frontend dependencies"
Commit-File "frontend/vite.config.js" "chore: Configure Vite and Tailwind v4 plugins"
Commit-File "frontend/index.html" "chore: Setup HTML entrypoint"
Commit-File "frontend/src/main.jsx" "feat: Setup React entry component"
Commit-File "frontend/src/index.css" "style: Setup Tailwind CSS base styles and fonts"
Commit-File "api.py" "feat: Create FastAPI backend server to serve agent logic"
Commit-File "frontend/src/App.jsx" "feat: Build basic React UI dashboard"
Commit-File "frontend/src/MemoryMatch.jsx" "feat: Implement Memory Match mini-game using Emojis"

# 25th commit adds everything else
git add .
git commit -m "style: Finalize premium dark mode aesthetic and polish UI"

git remote add origin https://github.com/Soujuhegde/Tech-Taco.git
