"""blender_rpc.py — Bicara LANGSUNG ke addon BlenderMCP di socket 9876,
melewati server MCP Claude yang sedang hang.

Diagnosa 16 Jun 2026: addon (port 9876, milik proses Blender) sehat & balas
<0.2s; yang rusak adalah proses server `blender-mcp` extension. Maka kita
pakai socket langsung.

Pakai sebagai modul:
    from tools.blender_rpc import run, call
    print(run("import bpy; print(bpy.app.version_string)"))
Atau CLI:
    python tools/blender_rpc.py "import bpy; print(len(bpy.data.objects))"
"""
import socket, json, sys, time

HOST, PORT = '127.0.0.1', 9876


def call(cmd: dict, recv_timeout: float = 120.0) -> dict:
    """Kirim 1 perintah JSON, kembalikan dict respons addon."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(8)
    s.connect((HOST, PORT))
    s.sendall(json.dumps(cmd).encode())
    s.settimeout(recv_timeout)
    buf = b''
    while True:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf.decode())
        except Exception:
            continue
    s.close()
    try:
        return json.loads(buf.decode())
    except Exception:
        return {'status': 'error', 'raw': buf.decode(errors='replace')}


def run(code: str, recv_timeout: float = 120.0) -> str:
    """Jalankan kode bpy di Blender; kembalikan STDOUT (pakai print untuk data)."""
    r = call({'type': 'execute_code', 'params': {'code': code}}, recv_timeout)
    if r.get('status') == 'success':
        res = r.get('result', {})
        out = res.get('result', '') if isinstance(res, dict) else ''
        return out if out else '[ok, no stdout]'
    return f"[ERROR] {json.dumps(r)[:500]}"


if __name__ == '__main__':
    code = sys.argv[1] if len(sys.argv) > 1 else "import bpy; print('Blender', bpy.app.version_string)"
    print(run(code))
