$npm = 'npm'
if (-not (Get-Command $npm -ErrorAction SilentlyContinue)) { throw 'npm is not installed' }
& $npm run dev
