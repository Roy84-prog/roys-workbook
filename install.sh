#!/bin/bash

# ==========================================
# Roy's Workbook 설치 스크립트
# macOS 전용 - 다른 맥에서 실행하세요
# ==========================================

set -e

APP_NAME="Roy's Workbook"
INSTALL_DIR="$HOME/RoysWorkbook"
VENV_DIR="$INSTALL_DIR/venv"
DESKTOP_APP="$HOME/Desktop/${APP_NAME}.app"
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.roys.workbook.plist"
PORT=8501

echo "=================================================="
echo "  📘 ${APP_NAME} 설치를 시작합니다"
echo "=================================================="
echo ""

# ------------------------------------------
# 1. Python 확인
# ------------------------------------------
echo "[1/6] Python 확인 중..."

if command -v python3 &>/dev/null; then
    PY=$(command -v python3)
    PY_VER=$($PY --version 2>&1)
    echo "  ✅ $PY_VER ($PY)"
else
    echo "  ❌ Python3가 설치되어 있지 않습니다."
    echo ""
    echo "  아래 방법 중 하나로 설치해주세요:"
    echo "    1) https://www.python.org/downloads/ 에서 다운로드"
    echo "    2) brew install python3"
    echo ""
    exit 1
fi

# ------------------------------------------
# 2. 프로젝트 폴더 생성
# ------------------------------------------
echo "[2/6] 프로젝트 설치 중..."

if [ -d "$INSTALL_DIR" ]; then
    echo "  ⚠️  기존 설치를 덮어씁니다: $INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"

# 소스 파일 복사 (이 스크립트와 같은 폴더에 있는 파일들)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/고등부 내신 교재 만들기.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

# .streamlit 설정
mkdir -p "$INSTALL_DIR/.streamlit"
if [ -f "$SCRIPT_DIR/.streamlit/config.toml" ]; then
    cp "$SCRIPT_DIR/.streamlit/config.toml" "$INSTALL_DIR/.streamlit/"
else
    cat > "$INSTALL_DIR/.streamlit/config.toml" << 'TOMLEOF'
[server]
headless = true
maxUploadSize = 50

[theme]
primaryColor = "#003b6f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#263238"
font = "sans serif"
TOMLEOF
fi

echo "  ✅ 파일 복사 완료: $INSTALL_DIR"

# ------------------------------------------
# 3. 가상환경 및 패키지 설치
# ------------------------------------------
echo "[3/6] 가상환경 생성 및 패키지 설치 중..."
echo "  (첫 설치 시 2~3분 소요될 수 있습니다)"

$PY -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip -q 2>/dev/null
pip install streamlit playwright -q 2>/dev/null

echo "  ✅ Python 패키지 설치 완료"

# ------------------------------------------
# 4. Playwright 브라우저 설치
# ------------------------------------------
echo "[4/6] PDF 변환용 브라우저 설치 중..."

playwright install chromium 2>/dev/null

echo "  ✅ Chromium 설치 완료"

# ------------------------------------------
# 5. 바탕화면 앱 생성
# ------------------------------------------
echo "[5/6] 바탕화면 앱 생성 중..."

STREAMLIT_PATH="$VENV_DIR/bin/streamlit"

# .app 번들 생성
mkdir -p "$DESKTOP_APP/Contents/MacOS"
mkdir -p "$DESKTOP_APP/Contents/Resources"

cat > "$DESKTOP_APP/Contents/Info.plist" << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleName</key>
    <string>Roy's Workbook</string>
    <key>CFBundleIdentifier</key>
    <string>com.roys.workbook.app</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
</dict>
</plist>
PLISTEOF

cat > "$DESKTOP_APP/Contents/MacOS/launcher" << LAUNCHEREOF
#!/bin/bash
STREAMLIT="${STREAMLIT_PATH}"
APP_DIR="${INSTALL_DIR}"
PORT=${PORT}
URL="http://localhost:\${PORT}"

if curl -s -o /dev/null -w "%{http_code}" "\$URL" 2>/dev/null | grep -q "200"; then
    open "\$URL"
    exit 0
fi

cd "\$APP_DIR"
source "${VENV_DIR}/bin/activate"
"\$STREAMLIT" run app.py --server.headless true --server.port "\$PORT" &
PID=\$!

for i in \$(seq 1 30); do
    if curl -s -o /dev/null -w "%{http_code}" "\$URL" 2>/dev/null | grep -q "200"; then
        open "\$URL"
        break
    fi
    sleep 0.5
done

wait \$PID
LAUNCHEREOF

chmod +x "$DESKTOP_APP/Contents/MacOS/launcher"

echo "  ✅ 바탕화면에 앱 생성 완료"

# ------------------------------------------
# 6. 자동 시작 설정
# ------------------------------------------
echo "[6/6] 맥 부팅 시 자동 시작 설정 중..."

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HOME/Library/Logs"

cat > "$LAUNCH_AGENT" << AGENTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.roys.workbook</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_DIR}/bin/streamlit</string>
        <string>run</string>
        <string>${INSTALL_DIR}/app.py</string>
        <string>--server.headless</string>
        <string>true</string>
        <string>--server.port</string>
        <string>${PORT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>VIRTUAL_ENV</key>
        <string>${VENV_DIR}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/roys-workbook.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/roys-workbook-error.log</string>
</dict>
</plist>
AGENTEOF

# 기존 서비스 중지 후 재시작
launchctl unload "$LAUNCH_AGENT" 2>/dev/null || true
launchctl load "$LAUNCH_AGENT"

echo "  ✅ 자동 시작 설정 완료"

# ------------------------------------------
# 완료
# ------------------------------------------
echo ""
echo "=================================================="
echo "  🎉 설치 완료!"
echo "=================================================="
echo ""
echo "  사용법:"
echo "    • 바탕화면의 'Roy's Workbook' 앱을 더블클릭"
echo "    • 또는 브라우저에서 http://localhost:${PORT} 접속"
echo ""
echo "  설치 위치: ${INSTALL_DIR}"
echo ""
echo "  제거하려면:"
echo "    bash ${INSTALL_DIR}/uninstall.sh"
echo ""
