#!/bin/bash

# ==========================================
# Roy's Workbook 제거 스크립트
# ==========================================

echo "📘 Roy's Workbook을 제거합니다..."

# 서비스 중지
launchctl unload "$HOME/Library/LaunchAgents/com.roys.workbook.plist" 2>/dev/null

# 파일 삭제
rm -f "$HOME/Library/LaunchAgents/com.roys.workbook.plist"
rm -rf "$HOME/Desktop/Roy's Workbook.app"
rm -rf "$HOME/RoysWorkbook"
rm -f "$HOME/Library/Logs/roys-workbook.log"
rm -f "$HOME/Library/Logs/roys-workbook-error.log"

echo "✅ 제거 완료!"
