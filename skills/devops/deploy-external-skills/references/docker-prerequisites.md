# Docker Prerequisites for Skill Deployment

Some external projects require Docker to run (open-notebook, open-LLM-VTUBER, etc.). This guide covers setting up Docker on an Ubuntu server, with Chinese mirror registry configuration.

## Ubuntu 24.04 Installation

### Step 1: Install Docker via official script

```bash
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
```

### Step 2: Add user to docker group

```bash
sudo usermod -aG docker $USER
# IMPORTANT: Group change only takes effect on NEW login sessions.
# Current terminal still needs `sudo docker` until logout/login.
# To run in current session: `newgrp docker` or `sg docker -c "<command>"`
```

### Step 3: Configure registry mirrors (China/GFW)

Docker Hub is often unreachable from Chinese networks. Configure mirrors:

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### Verify it works

```bash
docker run --rm hello-world
# Should print "Hello from Docker!" with no timeout errors
```

## Known Pitfalls

| Issue | Symptom | Fix |
|-------|---------|-----|
| **No mirror configured** | `i/o timeout` pulling images | Add daemon.json mirrors + restart |
| **Group not refreshed** | `permission denied` on docker socket | `newgrp docker` or logout/login |
| **Docker daemon not running** | `Cannot connect to Docker daemon` | `sudo systemctl start docker` |
| **Disk space** | `no space left on device` | `docker system prune -a` |

## After Docker is Ready

For projects that need Docker Compose (v2+ ships with `docker compose`):

```bash
docker compose version  # Should show v2+
docker compose up -d     # Start in background
docker compose logs -f   # Follow logs
docker compose down      # Stop and remove
```
