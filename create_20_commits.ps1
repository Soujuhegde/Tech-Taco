Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue

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
Commit-File "src/memory/embeddings.py" "feat: Implement local vector embeddings"
Commit-File "src/memory/vector_store.py" "feat: Build ChromaDB vector store"
Commit-File "src/agents/curator.py" "feat: Add Curator Agent for AI-driven news selection"
Commit-File "src/agents/writer.py" "feat: Add Writer Agent for drafting posts"
Commit-File "src/agents/graph.py" "feat: Connect agents using LangGraph state machine"
Commit-File "src/publishers/devto.py" "feat: Implement Dev.to API integration"
Commit-File "src/publishers/mastodon.py" "feat: Implement Mastodon API integration"
Commit-File "main.py" "feat: Create CLI entrypoint for the AI pipeline"
Commit-File ".github" "ci: Setup GitHub Actions cron job"
Commit-File "frontend/package.json" "chore: Initialize React Vite frontend project"
Commit-File "frontend/package-lock.json" "chore: Lock frontend dependencies"
Commit-File "frontend/src/index.css" "style: Setup Tailwind CSS base styles"
Commit-File "api.py" "feat: Create FastAPI backend server"

git add .
git commit -m "feat: Finalize Hacker Matrix UI and premium dashboard"

git remote add origin https://github.com/Soujuhegde/Tech-Taco.git
git push -u origin main --force
