cat > config.json << 'EOF'
{
  "blocked_apps": [
    "discord",
    "slack",
    "steam",
    "brave",
    "firefox",
    "signal"
  ],
  "check_interval": 0.5
}
EOF
echo "Created/reset config.json"
