#!/bin/bash
echo "⬇️ دانلود و نصب v2ray-core..."
wget https://github.com/v2fly/v2ray-core/releases/latest/download/v2ray-linux-64.zip -O v2ray.zip
unzip v2ray.zip -d v2ray
chmod +x v2ray/v2ray
chmod +x v2ray/v2ctl
echo "✅ v2ray-core نصب شد!"
