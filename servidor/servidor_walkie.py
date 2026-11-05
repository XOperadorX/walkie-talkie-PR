#!/usr/bin/env python3
"""Walkie-talkie server for a trusted local Wi-Fi network."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import socket
import socketserver
import struct
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
DATA_FILE = Path(os.environ.get("WALKIE_DATA_FILE", BASE_DIR / "usuarios.json"))
HOST = "0.0.0.0"
PORTA_SERVIDOR = int(os.environ.get("WALKIE_AUDIO_PORT", "5000"))
PORTA_WEB = int(os.environ.get("WALKIE_WEB_PORT", "8080"))
TAMANHO_MAXIMO_AUDIO = 8192
ITERACOES_HASH = 310_000

usuarios: dict[str, dict[str, str]] = {}
clientes: set[socket.socket] = set()
lock = threading.RLock()


def carregar_usuarios() -> None:
    global usuarios
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                usuarios = {str(k): v for k, v in raw.items() if isinstance(v, dict)}
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Não foi possível ler {DATA_FILE}: {exc}") from exc


def salvar_usuarios() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    temp.write_text(json.dumps(usuarios, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(DATA_FILE)


def gerar_id(nome: str) -> str:
    base = "".join(c.lower() if c.isalnum() else "-" for c in nome).strip("-")[:20] or "usuario"
    return f"{base}-{uuid.uuid4().hex[:8]}"


def criar_usuario(nome: str, senha: str) -> str:
    nome, senha = nome.strip(), senha
    if not 2 <= len(nome) <= 50:
        raise ValueError("O nome deve ter entre 2 e 50 caracteres.")
    if not 8 <= len(senha) <= 128:
        raise ValueError("A senha deve ter entre 8 e 128 caracteres.")
    salt = secrets.token_bytes(16)
    senha_hash = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES_HASH)
    with lock:
        uid = gerar_id(nome)
        usuarios[uid] = {"nome": nome, "salt": salt.hex(), "senha_hash": senha_hash.hex()}
        salvar_usuarios()
    return uid


def autenticar(uid: str, senha: str) -> bool:
    with lock:
        user = usuarios.get(uid)
        if not user:
            return False
        try:
            calculado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(user["salt"]), ITERACOES_HASH)
            return hmac.compare_digest(calculado.hex(), user["senha_hash"])
        except (KeyError, ValueError):
            return False


def receber_exato(sock: socket.socket, tamanho: int) -> bytes:
    partes = bytearray()
    while len(partes) < tamanho:
        bloco = sock.recv(tamanho - len(partes))
        if not bloco:
            raise ConnectionError("Conexão encerrada")
        partes.extend(bloco)
    return bytes(partes)


def receber_linha(sock: socket.socket, limite: int = 4096) -> bytes:
    linha = bytearray()
    while len(linha) <= limite:
        byte = sock.recv(1)
        if not byte:
            raise ConnectionError("Conexão encerrada")
        if byte == b"\n":
            return bytes(linha)
        linha.extend(byte)
    raise ConnectionError("Comando muito longo")


def enviar_json(sock: socket.socket, obj: dict) -> None:
    sock.sendall(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")


class AudioHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        sock = self.request
        uid = None
        sock.settimeout(30)
        try:
            linha = receber_linha(sock)
            if not linha:
                return
            try:
                comando = json.loads(linha.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                enviar_json(sock, {"status": "erro", "mensagem": "Comando inválido."})
                return
            uid = str(comando.get("id", ""))
            if comando.get("tipo") != "entrar" or not autenticar(uid, str(comando.get("senha", ""))):
                enviar_json(sock, {"status": "erro", "mensagem": "ID ou senha incorretos."})
                return
            enviar_json(sock, {"status": "ok", "mensagem": "Conectado à sala geral."})
            with lock:
                clientes.add(sock)
            while True:
                tamanho = struct.unpack("!I", receber_exato(sock, 4))[0]
                if not 1 <= tamanho <= TAMANHO_MAXIMO_AUDIO:
                    raise ConnectionError("Bloco de áudio inválido")
                audio = receber_exato(sock, tamanho)
                pacote = struct.pack("!I", tamanho) + audio
                with lock:
                    destinos = tuple(c for c in clientes if c is not sock)
                for destino in destinos:
                    try:
                        destino.sendall(pacote)
                    except OSError:
                        with lock:
                            clientes.discard(destino)
        except (OSError, ConnectionError, socket.timeout):
            pass
        finally:
            with lock:
                clientes.discard(sock)
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()


class AudioServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            conteudo = (WEB_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        elif self.path == "/download":
            apk = BASE_DIR / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
            if not apk.is_file():
                self.responder_html(404, "APK ainda não gerado", "Compile o projeto Android seguindo o README e tente novamente.")
                return
            conteudo = apk.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.android.package-archive")
            self.send_header("Content-Disposition", 'attachment; filename="walkie-talkie-debug.apk"')
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        else:
            self.responder_html(404, "Página não encontrada", "")

    def do_POST(self) -> None:
        if self.path != "/cadastrar":
            self.responder_html(404, "Página não encontrada", "")
            return
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= 4096:
                raise ValueError("Formulário inválido.")
            form = parse_qs(self.rfile.read(tamanho).decode("utf-8"), max_num_fields=5)
            nome = form.get("nome", [""])[0]
            senha = form.get("senha", [""])[0]
            uid = criar_usuario(nome, senha)
            self.responder_html(201, "Cadastro concluído", f"Seu ID de acesso é <strong>{uid}</strong>. Guarde-o junto com sua senha para entrar no aplicativo.", uid)
        except (ValueError, UnicodeDecodeError) as exc:
            self.responder_html(400, "Não foi possível cadastrar", str(exc))
        except OSError:
            self.responder_html(500, "Erro ao salvar cadastro", "Confira as permissões da pasta do servidor.")

    def responder_html(self, status: int, titulo: str, texto: str, uid: str = "") -> None:
        import html
        conteudo = f'''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(titulo)}</title><body style="font:16px Arial;max-width:620px;margin:4rem auto;padding:1rem;background:#f4f7fb;color:#16243a"><main style="background:white;padding:2rem;border-radius:16px"><h1>{html.escape(titulo)}</h1><p>{texto if uid else html.escape(texto)}</p>{f'<p><a href="/download">Baixar APK</a></p>' if uid else ''}<p><a href="/">Voltar</a></p></main></body></html>'''.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def log_message(self, formato: str, *args: object) -> None:
        print(f"[web] {self.client_address[0]} - {formato % args}")


def obter_ip_local() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main() -> None:
    carregar_usuarios()
    audio = AudioServer((HOST, PORTA_SERVIDOR), AudioHandler)
    threading.Thread(target=audio.serve_forever, name="audio", daemon=True).start()
    web = ThreadingHTTPServer((HOST, PORTA_WEB), WebHandler)
    print("Walkie-talkie ativo na rede local")
    print(f"Cadastro/download: http://{obter_ip_local()}:{PORTA_WEB}")
    print(f"Áudio TCP: porta {PORTA_SERVIDOR}")
    print("Mantenha esta janela aberta. Ctrl+C encerra o servidor.")
    try:
        web.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        web.server_close()
        audio.shutdown()
        audio.server_close()


if __name__ == "__main__":
    main()
