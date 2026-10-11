# 윈도우에서 실행: 최신 내용 받기 -> 내 변경 올리기
# 사용: powershell -ExecutionPolicy Bypass -File tools\sync.ps1 "메모(선택)"
param([string]$msg = "update")
Set-Location (Split-Path $PSScriptRoot -Parent)
git pull --rebase --autostash
if (-not $?) { Write-Host "받기 실패: 충돌을 먼저 해결하세요"; exit 1 }
if (git status --porcelain) {
  git add -A
  git commit -m "$msg / $env:COMPUTERNAME / $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}
git push
if ($?) { Write-Host "동기화 완료" }
