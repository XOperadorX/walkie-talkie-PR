#!/usr/bin/env python3
"""Walkie-talkie server for a trusted local Wi-Fi network."""
from __future__ import annotations

import base64
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
PORTA_DESCOBERTA = int(os.environ.get("WALKIE_DISCOVERY_PORT", "5001"))
SENHA_ADMIN = os.environ.get("WALKIE_ADMIN_PASSWORD", "")
TAMANHO_MAXIMO_AUDIO = 8192
TAMANHO_MAXIMO_CONTROLE = 16384
ITERACOES_HASH = 310_000

usuarios: dict[str, dict[str, str]] = {}
clientes: dict[socket.socket, dict[str, str]] = {}
chamadas_pendentes: dict[str, dict[str, object]] = {}
chamadas_ativas: dict[str, tuple[socket.socket, socket.socket]] = {}
chamada_por_cliente: dict[socket.socket, str] = {}
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


def enviar_pacote(sock: socket.socket, tipo: bytes, dados: bytes) -> None:
    if tipo not in (b"C", b"A") or not dados:
        raise ValueError("Pacote inválido")
    limite = TAMANHO_MAXIMO_CONTROLE if tipo == b"C" else TAMANHO_MAXIMO_AUDIO
    if len(dados) > limite:
        raise ValueError("Pacote muito grande")
    with lock:
        sock.sendall(tipo + struct.pack("!I", len(dados)) + dados)


def enviar_controle(sock: socket.socket, obj: dict) -> None:
    enviar_pacote(sock, b"C", json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def lista_usuarios_online() -> list[dict[str, str]]:
    por_id: dict[str, dict[str, str]] = {}
    for info in clientes.values():
        por_id[info["id"]] = {"id": info["id"], "nome": info["nome"]}
    return sorted(por_id.values(), key=lambda usuario: usuario["nome"].casefold())


def atualizar_usuarios_online() -> None:
    with lock:
        destinos = tuple(clientes)
        usuarios_online = lista_usuarios_online()
    for destino in destinos:
        try:
            enviar_controle(destino, {"tipo": "usuarios_online", "usuarios": usuarios_online})
        except OSError:
            pass


def encerrar_chamada(chamada_id: str, motivo: str) -> None:
    with lock:
        pendente = chamadas_pendentes.pop(chamada_id, None)
        ativa = chamadas_ativas.pop(chamada_id, None)
        if pendente:
            temporizador = pendente.get("temporizador")
            if isinstance(temporizador, threading.Timer):
                temporizador.cancel()
            participantes = (pendente["origem"], pendente["destino"])
        elif ativa:
            participantes = ativa
        else:
            return
        for participante in participantes:
            if isinstance(participante, socket.socket):
                chamada_por_cliente.pop(participante, None)
                if participante in clientes:
                    try:
                        enviar_controle(participante, {"tipo": "chamada_encerrada", "motivo": motivo})
                    except OSError:
                        pass


def remover_cliente(sock: socket.socket) -> None:
    """Drop a peer whose socket failed without dropping another caller."""
    with lock:
        chamada_id = chamada_por_cliente.get(sock)
        clientes.pop(sock, None)
    if chamada_id:
        encerrar_chamada(chamada_id, "conexao_perdida")
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass
    atualizar_usuarios_online()


def processar_controle(sock: socket.socket, mensagem: dict) -> None:
    comando = mensagem.get("tipo")
    if comando == "chamar":
        destino_id = str(mensagem.get("destino", ""))
        with lock:
            origem_info = clientes.get(sock)
            if not origem_info:
                return
            if sock in chamada_por_cliente:
                enviar_controle(sock, {"tipo": "erro", "mensagem": "Você já está em uma chamada."})
                return
            destino = next((cliente for cliente, info in clientes.items()
                            if info["id"] == destino_id and cliente is not sock
                            and cliente not in chamada_por_cliente), None)
            if not destino:
                print("[chamada] pedido recusado: a pessoa está offline ou ocupada")
                enviar_controle(sock, {"tipo": "erro", "mensagem": "Esse usuário não está disponível na rede agora."})
                return
            chamada_id = uuid.uuid4().hex
            destino_info = clientes[destino]
            temporizador = threading.Timer(35, encerrar_chamada, args=(chamada_id, "sem_resposta"))
            temporizador.daemon = True
            chamadas_pendentes[chamada_id] = {
                "origem": sock, "destino": destino, "temporizador": temporizador,
            }
            chamada_por_cliente[sock] = chamada_id
            chamada_por_cliente[destino] = chamada_id
            temporizador.start()
            try:
                enviar_controle(destino, {
                    "tipo": "convite", "chamada_id": chamada_id,
                    "origem_id": origem_info["id"], "origem_nome": origem_info["nome"],
                })
            except OSError:
                print("[chamada] o aparelho chamado perdeu a conexão; removendo-o da lista")
                remover_cliente(destino)
                return
            try:
                enviar_controle(sock, {
                    "tipo": "chamada_enviada", "chamada_id": chamada_id,
                    "destino_nome": destino_info["nome"],
                })
            except OSError:
                remover_cliente(sock)
                return
            print("[chamada] convite enviado para uma pessoa online")
        return

    chamada_id = str(mensagem.get("chamada_id", ""))
    with lock:
        pendente = chamadas_pendentes.get(chamada_id)
        if comando == "aceitar" and pendente and pendente["destino"] is sock:
            temporizador = pendente.get("temporizador")
            if isinstance(temporizador, threading.Timer):
                temporizador.cancel()
            chamadas_pendentes.pop(chamada_id, None)
            origem, destino = pendente["origem"], pendente["destino"]
            chamadas_ativas[chamada_id] = (origem, destino)
            try:
                enviar_controle(origem, {"tipo": "chamada_aceita", "chamada_id": chamada_id,
                                         "nome": clientes.get(destino, {}).get("nome", "Usuário")})
            except OSError:
                remover_cliente(origem)
                return
            try:
                enviar_controle(destino, {"tipo": "chamada_aceita", "chamada_id": chamada_id,
                                          "nome": clientes.get(origem, {}).get("nome", "Usuário")})
            except OSError:
                remover_cliente(destino)
                return
            print("[chamada] convite aceito; áudio privado liberado")
        elif comando in ("recusar", "cancelar", "encerrar"):
            participantes = chamadas_ativas.get(chamada_id)
            pendente_atual = chamadas_pendentes.get(chamada_id)
            participa = (participantes is not None and sock in participantes) or (
                pendente_atual is not None and sock in (pendente_atual["origem"], pendente_atual["destino"])
            )
            if participa:
                motivo = "recusada" if comando == "recusar" else "encerrada"
                encerrar_chamada(chamada_id, motivo)
            else:
                enviar_controle(sock, {"tipo": "erro", "mensagem": "Você não participa desta chamada."})
        else:
            enviar_controle(sock, {"tipo": "erro", "mensagem": "A solicitação de chamada não é mais válida."})


class AudioHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        sock = self.request
        uid = None
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
            with lock:
                nome = usuarios.get(uid, {}).get("nome", "Usuário")
            enviar_json(sock, {"status": "ok", "mensagem": "Autenticado."})
            with lock:
                sessoes_anteriores = tuple(
                    cliente for cliente, info in clientes.items() if info["id"] == uid
                )
            for sessao_antiga in sessoes_anteriores:
                print("[login] substituindo uma sessão anterior do mesmo ID")
                remover_cliente(sessao_antiga)
            with lock:
                clientes[sock] = {"id": uid, "nome": nome}
            atualizar_usuarios_online()
            while True:
                tipo = receber_exato(sock, 1)
                tamanho = struct.unpack("!I", receber_exato(sock, 4))[0]
                if tipo == b"C":
                    if not 1 <= tamanho <= TAMANHO_MAXIMO_CONTROLE:
                        raise ConnectionError("Comando inválido")
                    try:
                        controle = json.loads(receber_exato(sock, tamanho).decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        raise ConnectionError("Comando inválido")
                    if isinstance(controle, dict):
                        processar_controle(sock, controle)
                elif tipo == b"A":
                    if not 1 <= tamanho <= TAMANHO_MAXIMO_AUDIO:
                        raise ConnectionError("Bloco de áudio inválido")
                    audio = receber_exato(sock, tamanho)
                    with lock:
                        chamada_id = chamada_por_cliente.get(sock)
                        participantes = chamadas_ativas.get(chamada_id or "")
                        destino = next((cliente for cliente in participantes if cliente is not sock), None) if participantes else None
                    if destino:
                        try:
                            enviar_pacote(destino, b"A", audio)
                        except OSError:
                            remover_cliente(destino)
                else:
                    raise ConnectionError("Tipo de pacote inválido")
        except (OSError, ConnectionError, socket.timeout):
            pass
        finally:
            with lock:
                chamada_id = chamada_por_cliente.get(sock)
                clientes.pop(sock, None)
            if chamada_id:
                encerrar_chamada(chamada_id, "conexao_perdida")
            atualizar_usuarios_online()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()


class AudioServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class DiscoveryHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        pedido, sock = self.request
        if pedido.strip() != b"NEXTEL_LOCAL_DISCOVER_V1":
            return
        resposta = json.dumps({"service": "nextel-local", "port": PORTA_SERVIDOR}).encode("utf-8")
        sock.sendto(resposta, self.client_address)


class DiscoveryServer(socketserver.ThreadingUDPServer):
    allow_reuse_address = True
    daemon_threads = True


class WebHandler(BaseHTTPRequestHandler):
    def handle(self) -> None:
        # Browsers may close a tab or cancel a download while the server is
        # still reading/writing. That is a normal client disconnect.
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self) -> None:
        caminho = self.path.split("?", 1)[0]
        if caminho == "/api/admin/usuarios":
            if not self.autorizar_admin():
                return
            with lock:
                lista = [{"id": uid, "nome": dados.get("nome", "")} for uid, dados in usuarios.items()]
            lista.sort(key=lambda usuario: usuario["nome"].casefold())
            self.responder_json(200, {"usuarios": lista})
        elif caminho == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif caminho in ("/", "/index.html", "/inicio.html", "/cadastro.html", "/apk.html", "/adm_cadastro.html"):
            nome_pagina = "index.html" if caminho in ("/", "/index.html") else caminho[1:]
            conteudo = (WEB_DIR / nome_pagina).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        elif caminho == "/download":
            apk = BASE_DIR / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
            if not apk.is_file():
                self.responder_html(404, "APK ainda não gerado", "Compile o projeto Android seguindo o README e tente novamente.")
                return
            conteudo = apk.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.android.package-archive")
            self.send_header("Content-Disposition", 'attachment; filename="nextel-local-debug.apk"')
            self.send_header("Content-Length", str(len(conteudo)))
            self.end_headers()
            self.wfile.write(conteudo)
        else:
            self.responder_html(404, "Página não encontrada", "")

    def do_POST(self) -> None:
        if self.path == "/api/admin/usuarios":
            if not self.autorizar_admin():
                return
            try:
                dados = self.ler_json()
                uid = criar_usuario(str(dados.get("nome", "")), str(dados.get("senha", "")))
                self.responder_json(201, {"id": uid, "nome": usuarios[uid]["nome"]})
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self.responder_json(400, {"erro": str(exc) or "Dados inválidos."})
            except OSError:
                self.responder_json(500, {"erro": "Não foi possível salvar os usuários."})
            return
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

    def do_PUT(self) -> None:
        prefixo = "/api/admin/usuarios/"
        if not self.path.startswith(prefixo):
            self.responder_json(404, {"erro": "Rota não encontrada."})
            return
        if not self.autorizar_admin():
            return
        from urllib.parse import unquote
        uid = unquote(self.path[len(prefixo):])
        try:
            dados = self.ler_json()
            nome = str(dados.get("nome", "")).strip()
            if not 2 <= len(nome) <= 50:
                raise ValueError("O nome deve ter entre 2 e 50 caracteres.")
            senha = str(dados.get("senha", ""))
            with lock:
                usuario = usuarios.get(uid)
                if usuario is None:
                    self.responder_json(404, {"erro": "Cadastro não encontrado."})
                    return
                atualizado = {**usuario, "nome": nome}
                if senha:
                    if not 8 <= len(senha) <= 128:
                        raise ValueError("A senha deve ter entre 8 e 128 caracteres.")
                    salt = secrets.token_bytes(16)
                    atualizado["salt"] = salt.hex()
                    atualizado["senha_hash"] = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES_HASH).hex()
                usuarios[uid] = atualizado
                salvar_usuarios()
            self.responder_json(200, {"id": uid, "nome": nome})
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.responder_json(400, {"erro": str(exc) or "Dados inválidos."})
        except OSError:
            self.responder_json(500, {"erro": "Não foi possível salvar os usuários."})

    def do_DELETE(self) -> None:
        prefixo = "/api/admin/usuarios/"
        if not self.path.startswith(prefixo):
            self.responder_json(404, {"erro": "Rota não encontrada."})
            return
        if not self.autorizar_admin():
            return
        from urllib.parse import unquote
        uid = unquote(self.path[len(prefixo):])
        try:
            with lock:
                if uid not in usuarios:
                    self.responder_json(404, {"erro": "Cadastro não encontrado."})
                    return
                removido = usuarios.pop(uid)
                salvar_usuarios()
            self.responder_json(200, {"id": uid, "nome": removido.get("nome", "")})
        except OSError:
            self.responder_json(500, {"erro": "Não foi possível salvar os usuários."})

    def autorizar_admin(self) -> bool:
        if not SENHA_ADMIN:
            self.responder_json(503, {"erro": "Configure WALKIE_ADMIN_PASSWORD antes de usar a administração."})
            return False
        esperado = "Basic " + base64.b64encode(("admin:" + SENHA_ADMIN).encode("utf-8")).decode("ascii")
        if not hmac.compare_digest(self.headers.get("Authorization", ""), esperado):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Nextel Local - Administração", charset="UTF-8"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        return True

    def ler_json(self) -> dict:
        tamanho = int(self.headers.get("Content-Length", "0"))
        if not 0 < tamanho <= 4096:
            raise ValueError("Formulário inválido.")
        dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        if not isinstance(dados, dict):
            raise ValueError("Dados inválidos.")
        return dados

    def responder_json(self, status: int, dados: dict) -> None:
        conteudo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def responder_html(self, status: int, titulo: str, texto: str, uid: str = "") -> None:
        import html
        conteudo = f'''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(titulo)}</title><body style="font:16px Arial;max-width:620px;margin:2rem auto;padding:1rem;background:#f4f7fb;color:#16243a"><main style="background:white;padding:2rem;border-radius:16px"><nav style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem"><a href="/inicio.html">Início</a><a href="/cadastro.html">Criar acesso</a><a href="/apk.html">APK</a></nav><h1>{html.escape(titulo)}</h1><p>{texto if uid else html.escape(texto)}</p>{f'<p><a href="/apk.html">Ir para APK</a></p>' if uid else ''}</main></body></html>'''.encode()
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


def parar_servidor(servidor: socketserver.BaseServer) -> None:
    try:
        servidor.shutdown()
    except KeyboardInterrupt:
        # shutdown() has already requested the serve_forever loop to stop.
        # A second Ctrl+C should not prevent the listening socket from closing.
        print("\nInterrupção durante o encerramento; fechando o serviço.")
    finally:
        servidor.server_close()


def main() -> None:
    carregar_usuarios()
    audio = AudioServer((HOST, PORTA_SERVIDOR), AudioHandler)
    threading.Thread(target=audio.serve_forever, name="audio", daemon=True).start()
    descoberta = DiscoveryServer((HOST, PORTA_DESCOBERTA), DiscoveryHandler)
    threading.Thread(target=descoberta.serve_forever, name="descoberta", daemon=True).start()
    web = ThreadingHTTPServer((HOST, PORTA_WEB), WebHandler)
    print("Nextel Local (protótipo) ativo na rede Wi-Fi local")
    print(f"Cadastro/download: http://{obter_ip_local()}:{PORTA_WEB}")
    print(f"Áudio TCP: porta {PORTA_SERVIDOR}")
    print(f"Descoberta Wi-Fi UDP: porta {PORTA_DESCOBERTA}")
    print("Mantenha esta janela aberta. Ctrl+C encerra o servidor.")
    try:
        web.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        web.server_close()
        parar_servidor(audio)
        parar_servidor(descoberta)


if __name__ == "__main__":
    main()
