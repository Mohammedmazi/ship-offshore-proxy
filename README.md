#  Ship-Offshore Proxy System

A lightweight proxy system designed for cruise ships to minimize satellite internet costs by maintaining a **single persistent TCP connection** to an offshore proxy server. The system sequentially processes all HTTP and HTTPS requests through a custom-built proxy.

---

##  Problem Overview

The satellite internet provider charges the cruise ship based on the number of TCP connections. Therefore, **all HTTP(S) traffic must be tunneled through a single persistent connection** to reduce costs.

---

##  Components

### 1. `ship_proxy_client.py`
- Acts as the local HTTP/HTTPS proxy for client devices onboard.
- Listens on port `8080`.
- Forwards requests one-by-one over a single TCP connection to the offshore proxy.

### 2. `offshore_proxy_server.py`
- Receives framed requests over the persistent TCP connection.
- Processes HTTP requests directly and establishes tunnels for HTTPS.

---
## command to run the client and server via docker

docker pull mazin01/offshore-proxy:latest
docker pull mazin01/ship-proxy:latest

docker network create proxy-net

docker run -d --name offshore_proxy --network proxy-net -p 9999:9999 mazin01/offshore-proxy:latest

docker run -d --name ship_proxy --network proxy-net -p 8080:8080 mazin01/ship-proxy:latest

curl -x http://localhost:8080 http://example.com

curl -x http://localhost:8080 https://example.com

docker rm -f ship_proxy offshore_proxy

docker network rm proxy-net
## test commands
-- curl.exe -x http://localhost:8080 https://example.com/
-- curl.exe -x http://localhost:8080 https://example.com/
-- curl.exe -x http://localhost:8080 http://neverssl.com/
---   
