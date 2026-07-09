#!/bin/zsh
# Install the two managed agents (watcher 08:00, cleaner 08:15) as user LaunchAgents.
set -e
mkdir -p "$(dirname "$0")/../logs"
for a in watcher cleaner; do
  cp "$(dirname "$0")/com.agenticgtm.$a.plist" ~/Library/LaunchAgents/
  launchctl unload ~/Library/LaunchAgents/com.agenticgtm.$a.plist 2>/dev/null || true
  launchctl load ~/Library/LaunchAgents/com.agenticgtm.$a.plist
done
echo "installed:"
launchctl list | grep agenticgtm
