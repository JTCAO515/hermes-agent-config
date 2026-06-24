# Headless OpenD Deployment (Cloud Server / No GUI)

When deploying Futu OpenD on a cloud server without a display (e.g., Ubuntu VPS), use Xvfb to provide a virtual framebuffer.

## Step-by-step

### 1. Install dependencies
```bash
sudo apt-get install -y xvfb x11vnc xdotool
```

### 2. Start virtual display
```bash
# Kill any existing instances first
pkill -f "Futu_OpenD" 2>/dev/null
pkill -f "Xvfb" 2>/dev/null

# Start Xvfb on display :99
Xvfb :99 -screen 0 1280x720x24 &
```

### 3. Start OpenD on virtual display
```bash
DISPLAY=:99 nohup Futu_OpenD > /tmp/opend.log 2>&1 &
```

### 4. Verify OpenD is running
```bash
# Check process
pgrep -a Futu_OpenD

# Check log
tail -20 /tmp/opend.log

# Port 11111 will NOT be open until user logs in through GUI
ss -tlnp | grep 11111
```

### 5. Provide remote GUI access (VNC)

For the user to log in, they need to see the OpenD GUI. Two options:

**Option A: x11vnc (direct VNC)**
```bash
x11vnc -display :99 -forever -nopw -quiet -listen 0.0.0.0 -rfbport 5900 &
```
User connects with any VNC client to `server-ip:5900`, no password.

**Option B: noVNC (browser-based, recommended)**
```bash
sudo apt-get install -y novnc websockify
websockify --web=/usr/share/novnc 6080 127.0.0.1:5900 &
```
User opens `http://server-ip:6080/vnc.html` in any browser.

### 6. Firewall / Security Group

Make sure the cloud firewall allows:
- **VNC**: TCP 5900
- **noVNC**: TCP 6080

### Troubleshooting

| Symptom | Solution |
|---------|---------|
| OpenD not starting | Check log: `tail -50 /tmp/opend.log`. Missing Qt dependencies? Install: `sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 libxcb-xfixes0 libxcb-xkb1 libxkbcommon-x11-0` |
| VNC connection refused | Check firewall allows port 5900. Verify `ss -tlnp | grep 5900` |
| Port 11111 not open | This is normal — OpenD only opens the API port AFTER login. User must VNC in and log in first. |
| SDK connection times out | Check protobuf version: must be 3.x not 5.x/6.x. `pip3 install "protobuf>=3.0,<4.0"` |
