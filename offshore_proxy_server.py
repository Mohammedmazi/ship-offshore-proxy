# === offshore_proxy_server.py ===
import socket
import struct
import threading

def debug(msg):
    print(f"[OFFSHORE] {msg}")

def recv_framed(conn):
    header = conn.recv(4)
    if not header:
        debug("Missing framed header")
        return None
    length = struct.unpack('!I', header)[0]
    debug(f"Receiving {length} bytes framed request")
    data = b''
    while len(data) < length:
        chunk = conn.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def send_framed(conn, data):
    debug(f"Sending {len(data)} bytes framed response")
    conn.sendall(struct.pack('!I', len(data)) + data)

def relay(src, dst, label):
    src.settimeout(30)
    try:
        while True:
            try:
                data = src.recv(4096)
                if not data:
                    debug(f"{label} connection closed.")
                    break
                debug(f"Relaying {len(data)} bytes from {label}")
                dst.sendall(data)
            except socket.timeout:
                debug(f"{label} timed out.")
                break
    except Exception as e:
        debug(f"Relay error ({label}): {e}")
    finally:
        try: src.shutdown(socket.SHUT_RD)
        except: pass
        try: dst.shutdown(socket.SHUT_WR)
        except: pass

def process_requests(conn):
    debug("Started processing client requests")
    while True:
        req = recv_framed(conn)
        if not req:
            debug("No request received or connection closed")
            break

        try:
            if req.startswith(b"CONNECT"):
                line = req.decode().splitlines()[0]
                addr = line.split()[1]
                host, port = addr.split(":")
                debug(f"Establishing tunnel to {host}:{port}")
                remote = socket.create_connection((host, int(port)))
                send_framed(conn, b"HTTP/1.1 200 Connection Established\r\n\r\n")

                t1 = threading.Thread(target=relay, args=(conn, remote, "ship->remote"), daemon=True)
                t2 = threading.Thread(target=relay, args=(remote, conn, "remote->ship"), daemon=True)
                t1.start()
                t2.start()
                t1.join(timeout=30)
                t2.join(timeout=30)

                debug("HTTPS tunnel closed. Returning to request loop.")

            else:
                lines = req.decode().splitlines()
                url = lines[0].split()[1]
                debug(f"HTTP URL: {url}")
                if url.startswith("http://"):
                    url = url[7:]
                host = url.split("/")[0]
                path = url[len(host):] or "/"

                remote = socket.create_connection((host, 80))
                lines[0] = f"GET {path} HTTP/1.1"
                headers = [l for l in lines if not l.lower().startswith("proxy-connection")]
                headers.append("Connection: close")
                if not any(h.lower().startswith("host:") for h in headers):
                    headers.insert(1, f"Host: {host}")
                new_req = "\r\n".join(headers) + "\r\n\r\n"
                remote.sendall(new_req.encode())

                resp = b""
                while True:
                    chunk = remote.recv(4096)
                    if not chunk:
                        break
                    resp += chunk
                send_framed(conn, resp)
                remote.close()

                debug("HTTP response relayed back to ship.")

        except Exception as e:
            debug(f"Exception: {e}")
            try:
                send_framed(conn, b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except:
                pass

        debug("Waiting for next request...")

def start_proxy():
    debug("Offshore proxy listening on port 9999")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 9999))
    server.listen(1)
    while True:
        conn, _ = server.accept()
        debug("New connection from ship proxy")
        threading.Thread(target=process_requests, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    start_proxy()
