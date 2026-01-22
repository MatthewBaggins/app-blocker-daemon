cat > config.json << 'EOF'
{
  "blocked_apps": [
    "discord",
    "slack",
    "steam",
    "brave",
    "brave-browser",
    "firefox"
  ],
  "check_interval": 0.5
}
EOF
echo "Created/reset config.json"
