# Proxy 故障排查速查

## 判断代理类型

```bash
# 测试 HTTP CONNECT 代理
curl -x http://127.0.0.1:10809 -s --max-time 5 https://api.github.com -o /dev/null -w "%{http_code}"

# 测试 SOCKS5 代理（Xray 通常只开 HTTP CONNECT）
curl -x socks5://127.0.0.1:10809 -s --max-time 5 https://api.github.com -o /dev/null -w "%{http_code}"

# 200 = 正常, 000 = 不通/超时
```

## 常见失败模式

| 现象 | 诊断 | 解决 |
|------|------|------|
| git clone 成功但 push 失败 | 代理对大文件推送超时 | 先初始化 repo，再 force push |
| git clone/push 都失败 | 代理未设置或已断开 | 检查 `echo $http_proxy` / 重启 Xray |
| curl 走代理成功，git 失败 | git 未读取代理变量 | `git config --global http.proxy` |
| 某些 API 走代理超时 | 目标服务器被代理限流 | 绕过代理：`--noproxy '*'` |

## 网络诊断三板斧

```bash
# 1. 代理本身是否活着
curl -x http://127.0.0.1:10809 -s --max-time 5 https://www.google.com -o /dev/null -w "%{http_code}"

# 2. 直接连接是否可用  
curl -s --noproxy '*' --max-time 5 https://api.github.com -o /dev/null -w "%{http_code}"

# 3. DNS 是否解析
host github.com
```
