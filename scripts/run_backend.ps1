$python = 'C:\Users\W\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
& $python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

