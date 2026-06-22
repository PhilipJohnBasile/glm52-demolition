#!/bin/bash
# Permanently raise the Apple-Silicon GPU memory ceiling so the 99 GB GLM-5.2 model has
# KV-cache headroom (fixes the Metal OOM / timeout crashes — model is 101.6 GB vs the
# default ~110 GB cap). Sets it now AND installs a LaunchDaemon so it survives reboots.
#
#   sudo bash dist/install_gpu_limit.sh        # install + apply
#   sudo bash dist/install_gpu_limit.sh undo   # uninstall + revert to default
set -e
PLIST=/Library/LaunchDaemons/com.glm52.gpulimit.plist
LIMIT=122000   # MB (122 GB; leaves ~6 GB for macOS on a 128 GB machine)

if [ "$(id -u)" != "0" ]; then
  echo "  run with sudo:  sudo bash dist/install_gpu_limit.sh"; exit 1
fi

if [ "$1" = "undo" ]; then
  launchctl bootout system "$PLIST" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  sysctl iogpu.wired_limit_mb=0   # 0 = back to system default
  echo "  uninstalled; GPU limit reverted to system default"
  exit 0
fi

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.glm52.gpulimit</string>
  <key>ProgramArguments</key>
  <array><string>/usr/sbin/sysctl</string><string>iogpu.wired_limit_mb=${LIMIT}</string></array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
EOF
chown root:wheel "$PLIST"
chmod 644 "$PLIST"
launchctl bootstrap system "$PLIST" 2>/dev/null || launchctl load -w "$PLIST" 2>/dev/null || true
sysctl iogpu.wired_limit_mb=${LIMIT}    # apply right now too
echo "  installed + applied: iogpu.wired_limit_mb=${LIMIT} (persists across reboots)"
echo "  verify:  sysctl iogpu.wired_limit_mb"
