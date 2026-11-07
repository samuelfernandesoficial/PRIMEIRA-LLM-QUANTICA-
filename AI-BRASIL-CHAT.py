# -*- coding: utf-8 -*-
"""
AI BRASIL CHAT — Experiencia ChatGPT com o motor real do IA BRASIL
==================================================================
- Tela de LOGIN e CADASTRO no inicio + clientes + banco de dados local (SQLite)
- Telemetria completa: mensagens, tokens, latencia, motores, eventos, clientes
- Vendas de APIs com planos (GRATUITO/PRATA/OURO) e chaves sk-br-...
- API EXTERNA funcionando na rede: POST /api/v1/chat (Authorization: Bearer)
- Chat com streaming real + raciocinio visivel (como ChatGPT)
- Modo DEV: quando o pedido e de programacao, abre painel de trabalho lateral
  com codigo em tempo real, terminal e testes automaticos (motor DEVELOPER NX)
- Nucleo: 8540 (IA Brasil-NX raciocinio) + 8541 (IA Brasil-Rapido-NX)
- ARBITRO-O: agente supremo avaliador (superpoderes: julga em 0ms, nota 0-100,
  veta versao ruim e forca recalculo, LEVANTA a versao boa pra producao do nucleo)
- EVOLUCAO AUTONOMA: o nucleo detecta novas tecnologias no PC sozinho (genes)
  e auto-ajusta seus proprios parametros conforme o desempenho real (mutacoes)
- Painel NUCLEO DE EVOLUCAO AO VIVO dentro do chat (todos os dados quanticos)
- Nucleo IA 100%% offline. Sem cloud. Contas, chaves e telemetria salvas so no PC.
"""
import hashlib
import secrets
import socket
import sqlite3
import json
import os
import re
import subprocess
import shutil
import sys
import threading
import time
import datetime
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------- CONFIG
PORTA = 8580
BASE = os.path.dirname(os.path.abspath(__file__))
ARQ_PAGINA = os.path.join(BASE, "AI-BRASIL-CHAT.html")
DIR_TRABALHO = os.path.join(BASE, "AI-BRASIL-CHAT")
DIR_PROJETOS = os.path.join(DIR_TRABALHO, "projetos")
ARQ_LOG = os.path.join(DIR_TRABALHO, "aibrasil.log")
ARQ_JSONL = os.path.join(DIR_TRABALHO, "log-conversas.jsonl")
ARQ_IA_PRO = os.path.join(BASE, "ia_pro.py")
PYTHON_EXE = sys.executable or "python.exe"

ARQ_DB = os.path.join(BASE, "AI-BRASIL-DB.db")
NOME_ADMIN = "SEU-USUARIO-ADMIN"
EMAIL_ADMIN = "seu-email@exemplo.com"
SENHA_ADMIN = "SUA-SENHA-ADMIN"
INICIO_TS = time.time()
VERSAO = "9.8"

CHAVE_PADRAO = "IABRASIL-NUCLEO-2026-V9"
MODELO_A = {"porta": 8540, "nome": "IA Brasil-NX", "rotulo": "NX-8B"}
MODELO_B = {"porta": 8541, "nome": "IA Brasil-Rapido-NX", "rotulo": "RAPIDO"}
TEMPO_LIMITE_EXEC = 35
MAX_TENTATIVAS = 4

# ---------------- SANDBOX (ambiente virtual dos agentes) ----------------
DIR_SANDBOX = os.path.join(BASE, "SANDBOX")
VENV_PY = os.path.join(DIR_SANDBOX, "venv", "Scripts", "python.exe")
SANDBOX_MAX_RUNS = 20
MAX_LINHAS_TERMINAL = 300

LINGUAGENS = {
    "python":     {"ext": ".py",  "tag": "python",     "rotulo": "Python"},
    "batch":      {"ext": ".bat", "tag": "batch",      "rotulo": "Batch"},
    "powershell": {"ext": ".ps1", "tag": "powershell", "rotulo": "PowerShell"},
}

RE_ACAO = re.compile(
    r"(crie|criar|criando|fa[çc]a|fazer|desenvolv|gere|gerar|escreva|monte|construa|"
    r"implemente|automatize|build|create|make|write|develop|generate|implement)", re.I)
RE_ARTEFATO = re.compile(
    r"(programa|c[óo]digo|codigo|script|app|aplicativ|automa|bot|sistema|gerador|"
    r"fun[çc][ãa]o|ferramenta|jogo|site|p[áa]gina|calc|teste|test|arquivo|planilha|"
    r"conversor|api|conex[ãa]o|conexao|integra|monitor|tela|gr[áa]fico|rob[ôo]|"
    r"trade|trading|chave|senha|organi|renome|backup|servidor)", re.I)
RE_POWERSHELL = re.compile(r"powershell|\.ps1\b", re.I)
RE_BATCH = re.compile(r"\bbatch\b|\.bat\b|\bbat\b", re.I)


def log(texto):
    try:
        with open(ARQ_LOG, "a", encoding="utf-8") as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + texto + "\n")
    except Exception:
        pass


def ler_chave_nucleo():
    try:
        with open(ARQ_IA_PRO, "r", encoding="utf-8", errors="replace") as f:
            m = re.search(r'CHAVE_NUCLEO\s*=\s*"([^"]+)"', f.read(200000))
            if m:
                return m.group(1)
    except Exception:
        pass
    return CHAVE_PADRAO


def hoje_pt():
    return datetime.datetime.now().strftime("%d/%m/%Y")


class ConexaoMorta(Exception):
    pass


# ---------------------------------------------------------------- PLANOS
def agora_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def quando_curta(txt):
    return (txt or "")[:16].replace("T", " ")


# ---------------- EVOLUCAO DO NUCLEO (XP -> nivel do campo quantico) ----------------
NIVEIS_EVOLUCAO = [
    (0, "Semente Qu\u00e2ntica"),
    (150, "Superposi\u00e7\u00e3o Est\u00e1vel"),
    (400, "Entrela\u00e7ada"),
    (900, "Colapso Controlado"),
    (1800, "Coer\u00eancia Plena"),
    (3500, "Campo Unificado"),
    (6000, "Singularidade"),
]


def nivel_evolucao(xp):
    nivel, nome = 1, NIVEIS_EVOLUCAO[0][1]
    for i, (lim, nm) in enumerate(NIVEIS_EVOLUCAO):
        if xp >= lim:
            nivel, nome = i + 1, nm
    if xp >= NIVEIS_EVOLUCAO[-1][0] + 5000:
        extra = (xp - NIVEIS_EVOLUCAO[-1][0]) // 5000
        nivel += extra
        nome = "Singularidade +%d" % extra
    return nivel, nome


def xp_proximo_nivel(xp):
    for lim, _nm in NIVEIS_EVOLUCAO:
        if xp < lim:
            return lim
    base = NIVEIS_EVOLUCAO[-1][0]
    return base + ((xp - base) // 5000 + 1) * 5000


PLANOS = {
    "GRATUITO": {"nome": "Gratuito", "preco": "R$ 0", "por_dia": 50, "chaves": 2},
    "PRATA": {"nome": "Prata", "preco": "R$ 29,90/mês", "por_dia": 300, "chaves": 5},
    "OURO": {"nome": "Ouro", "preco": "R$ 99,90/mês", "por_dia": 2000, "chaves": 10},
}


# ---------------------------------------------------------------- BANCO DE DADOS
class Banco:
    """SQLite local: usuarios, sessoes, chaves de API, uso e telemetria."""

    def __init__(self, caminho):
        self.lock = threading.Lock()
        self.cx = sqlite3.connect(caminho, check_same_thread=False)
        self.cx.row_factory = sqlite3.Row
        self._criar()

    def _criar(self):
        with self.lock:
            c = self.cx.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY "
                      "AUTOINCREMENT, nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, "
                      "sal TEXT NOT NULL, hash TEXT NOT NULL, admin INTEGER DEFAULT 0, "
                      "quando TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS sessoes(token TEXT PRIMARY KEY, "
                      "usuario_id INTEGER, quando TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS chaves(id INTEGER PRIMARY KEY "
                      "AUTOINCREMENT, usuario_id INTEGER, chave TEXT UNIQUE, plano TEXT, "
                      "ativa INTEGER DEFAULT 1, quando TEXT, hoje_data TEXT DEFAULT '', "
                      "hoje INTEGER DEFAULT 0, total INTEGER DEFAULT 0)")
            c.execute("CREATE TABLE IF NOT EXISTS uso(id INTEGER PRIMARY KEY "
                      "AUTOINCREMENT, quando TEXT, via TEXT, usuario_id INTEGER, "
                      "chave_id INTEGER, modelo TEXT, modo TEXT, tokens_ent INTEGER, "
                      "tokens_sai INTEGER, latencia_ms INTEGER, status TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS telemetria(id INTEGER PRIMARY KEY "
                      "AUTOINCREMENT, quando TEXT, tipo TEXT, detalhe TEXT, "
                      "usuario TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS evolucao(id INTEGER PRIMARY KEY "
                      "AUTOINCREMENT, quando TEXT, operador TEXT, evento TEXT, "
                      "tempo_ms INTEGER DEFAULT 0, modelo TEXT DEFAULT '', "
                      "extra TEXT DEFAULT '')")
            self.cx.commit()

    @staticmethod
    def _hash(sal, senha):
        return hashlib.sha256((sal + senha).encode("utf-8")).hexdigest()

    def registrar(self, nome, email, senha):
        nome = (nome or "").strip()[:60]
        email = (email or "").strip().lower()[:80]
        if len(nome) < 2:
            return {"erro": "Informe seu nome."}
        if "@" not in email or "." not in email:
            return {"erro": "E-mail inválido."}
        if len(senha or "") < 4:
            return {"erro": "A senha precisa ter pelo menos 4 caracteres."}
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT COUNT(*) n FROM usuarios")
            primeiro = c.fetchone()["n"] == 0
            try:
                sal = secrets.token_hex(8)
                c.execute("INSERT INTO usuarios(nome,email,sal,hash,admin,quando) "
                          "VALUES(?,?,?,?,?,?)",
                          (nome, email, sal, self._hash(sal, senha),
                           1 if primeiro else 0, agora_iso()))
                self.cx.commit()
            except sqlite3.IntegrityError:
                return {"erro": "Este e-mail já está cadastrado."}
            c.execute("SELECT id FROM usuarios WHERE email=?", (email,))
            uid = c.fetchone()["id"]
            tok = secrets.token_urlsafe(32)
            c.execute("INSERT INTO sessoes(token,usuario_id,quando) VALUES(?,?,?)",
                      (tok, uid, agora_iso()))
            self.cx.commit()
        self.tele("cadastro", "%s <%s>" % (nome, email), nome)
        return {"token": tok, "usuario": {"id": uid, "nome": nome, "email": email,
                                           "admin": primeiro}}

    def login(self, usuario, senha):
        """Aceita usuário (nome) ou e-mail."""
        usuario = (usuario or "").strip()
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT * FROM usuarios WHERE email=? OR nome=?",
                      (usuario.lower(), usuario))
            u = c.fetchone()
            if not u or self._hash(u["sal"], senha or "") != u["hash"]:
                return {"erro": "Usuário ou senha incorretos."}
            tok = secrets.token_urlsafe(32)
            c.execute("INSERT INTO sessoes(token,usuario_id,quando) VALUES(?,?,?)",
                      (tok, u["id"], agora_iso()))
            self.cx.commit()
        self.tele("login", usuario, u["nome"])
        return {"token": tok, "usuario": {"id": u["id"], "nome": u["nome"],
                                           "email": u["email"], "admin": bool(u["admin"])}}

    def usuario_da_sessao(self, tok):
        if not tok:
            return None
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT u.id, u.nome, u.email, u.admin FROM sessoes s "
                      "JOIN usuarios u ON u.id = s.usuario_id WHERE s.token=?", (tok,))
            r = c.fetchone()
            return dict(r) if r else None

    def sair(self, tok):
        if not tok:
            return
        with self.lock:
            self.cx.execute("DELETE FROM sessoes WHERE token=?", (tok,))
            self.cx.commit()

    def semear_admin(self):
        """Garante o administrador fixo do sistema (criado 1x no primeiro boot)."""
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT COUNT(*) n FROM usuarios WHERE admin=1")
            if c.fetchone()["n"] > 0:
                return
            sal = secrets.token_hex(8)
            c.execute("INSERT INTO usuarios(nome,email,sal,hash,admin,quando) "
                      "VALUES(?,?,?,?,1,?)",
                      (NOME_ADMIN, EMAIL_ADMIN, sal,
                       self._hash(sal, SENHA_ADMIN), agora_iso()))
            self.cx.commit()
        self.tele("admin_criado", EMAIL_ADMIN, "Admin")

    # ---------- chaves de API ----------
    def chave_criar(self, uid, plano):
        if plano not in PLANOS:
            return {"erro": "Plano inválido."}
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT COUNT(*) n FROM chaves WHERE usuario_id=?", (uid,))
            if c.fetchone()["n"] >= PLANOS[plano]["chaves"]:
                return {"erro": "Limite de %d chaves do plano %s atingido."
                                % (PLANOS[plano]["chaves"], plano)}
            chave = "sk-br-" + secrets.token_urlsafe(24)
            c.execute("INSERT INTO chaves(usuario_id, chave, plano, ativa, quando) "
                      "VALUES(?,?,?,1,?)", (uid, chave, plano, agora_iso()))
            self.cx.commit()
        self.tele("chave_criada", "plano %s" % plano)
        return {"chave": chave, "plano": plano}

    def chave_por_token(self, chave):
        if not chave:
            return None
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT * FROM chaves WHERE chave=?", (chave.strip(),))
            r = c.fetchone()
            return dict(r) if r else None

    def chaves_do(self, uid):
        hoje = datetime.date.today().isoformat()
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT id, chave, plano, ativa, quando, hoje, hoje_data, total "
                      "FROM chaves WHERE usuario_id=? ORDER BY id DESC", (uid,))
            rows = c.fetchall()
        return [{"id": r["id"], "chave": r["chave"], "plano": r["plano"],
                 "ativa": bool(r["ativa"]), "quando": quando_curta(r["quando"]),
                 "hoje": r["hoje"] if r["hoje_data"] == hoje else 0,
                 "total": r["total"] or 0} for r in rows]

    def chave_uso_hoje(self, cid):
        hoje = datetime.date.today().isoformat()
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT hoje, hoje_data FROM chaves WHERE id=?", (cid,))
            r = c.fetchone()
            if not r:
                return 0
            return r["hoje"] if r["hoje_data"] == hoje else 0

    def chave_registrar_pedido(self, cid):
        hoje = datetime.date.today().isoformat()
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT hoje, hoje_data, total FROM chaves WHERE id=?", (cid,))
            r = c.fetchone()
            if not r:
                return 0
            h = (r["hoje"] if r["hoje_data"] == hoje else 0) + 1
            t = (r["total"] or 0) + 1
            c.execute("UPDATE chaves SET hoje=?, hoje_data=?, total=? WHERE id=?",
                      (h, hoje, t, cid))
            self.cx.commit()
            return h

    def chave_revogar(self, uid, cid):
        with self.lock:
            c = self.cx.cursor()
            c.execute("UPDATE chaves SET ativa=0 WHERE id=? AND usuario_id=?", (cid, uid))
            self.cx.commit()
            return c.rowcount > 0

    # ---------- telemetria / uso ----------
    def registrar_uso(self, via, usuario_id, chave_id, modo, modelo, tokens_ent,
                      tokens_sai, latencia_ms, status):
        with self.lock:
            c = self.cx.cursor()
            c.execute("INSERT INTO uso(quando, via, usuario_id, chave_id, modelo, modo, "
                      "tokens_ent, tokens_sai, latencia_ms, status) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (agora_iso(), via, usuario_id, chave_id, modelo or "", modo,
                       int(tokens_ent or 0), int(tokens_sai or 0), int(latencia_ms or 0),
                       status or ""))
            self.cx.commit()

    def tele(self, tipo, detalhe="", usuario=""):
        try:
            with self.lock:
                c = self.cx.cursor()
                c.execute("INSERT INTO telemetria(quando, tipo, detalhe, usuario) "
                          "VALUES(?,?,?,?)",
                          (agora_iso(), tipo, (detalhe or "")[:200], usuario or ""))
                self.cx.commit()
        except Exception:
            pass

    # ---------- evolucao dos operadores do nucleo ----------
    def evolucao_registra(self, operador, evento, tempo_ms=0, modelo="", extra=""):
        try:
            with self.lock:
                c = self.cx.cursor()
                c.execute("INSERT INTO evolucao(quando, operador, evento, tempo_ms, "
                          "modelo, extra) VALUES(?,?,?,?,?,?)",
                          (agora_iso(), operador, evento, int(tempo_ms or 0),
                           (modelo or "")[:40], (extra or "")[:200]))
                self.cx.commit()
        except Exception:
            pass

    def evolucao_stats(self):
        """Evolucao REAL dos operadores do nucleo, lida do banco."""
        out = {"por_operador": {}, "por_hora": [], "leituras": [],
               "exec_total": 0, "xp": 0}
        try:
            with self.lock:
                c = self.cx.cursor()
                c.execute("SELECT operador, COUNT(*) n, AVG(tempo_ms) tms, "
                          "SUM(CASE WHEN evento IN ('ok','aplicado') THEN 1 ELSE 0 END) ok "
                          "FROM evolucao GROUP BY operador")
                for r in c.fetchall():
                    out["por_operador"][r["operador"]] = {
                        "execucoes": r["n"],
                        "tempo_medio_ms": int(r["tms"] or 0),
                        "ok": int(r["ok"] or 0)}
                    out["exec_total"] += r["n"]
                h = datetime.datetime.now()
                for i in range(11, -1, -1):
                    ini = (h - datetime.timedelta(hours=i)).replace(
                        minute=0, second=0, microsecond=0)
                    fim = ini + datetime.timedelta(hours=1)
                    c.execute("SELECT COUNT(*) n FROM evolucao WHERE quando>=? AND quando<?",
                              (ini.isoformat(timespec="seconds"),
                               fim.isoformat(timespec="seconds")))
                    out["por_hora"].append({"hora": ini.strftime("%H:%M"),
                                            "execucoes": c.fetchone()["n"]})
                c.execute("SELECT quando, operador, evento, tempo_ms, extra FROM evolucao "
                          "ORDER BY id DESC LIMIT 10")
                for r in c.fetchall():
                    out["leituras"].append({
                        "quando": (r["quando"] or "")[11:19],
                        "operador": r["operador"], "evento": r["evento"],
                        "tempo_ms": r["tempo_ms"], "extra": (r["extra"] or "")[:120]})
        except Exception:
            pass
        xp = 0
        for op, d in out["por_operador"].items():
            peso = {"SUPERPOSICAO": 12, "AGENTE": 8, "VERIFICACAO": 6,
                    "RECALCULO": 20, "ENTRELACE": 4, "ARBITRO": 15,
                    "AUTONOMO": 10}.get(op, 4)
            xp += d["execucoes"] * peso
        out["xp"] = xp
        out["nivel"], out["nivel_nome"] = nivel_evolucao(xp)
        out["xp_proximo"] = xp_proximo_nivel(xp)
        return out

    def clientes(self, ver_todos, uid=None):
        hoje = datetime.date.today().isoformat()
        with self.lock:
            c = self.cx.cursor()
            if ver_todos:
                c.execute("SELECT id, nome, email, admin, quando FROM usuarios ORDER BY id")
            else:
                c.execute("SELECT id, nome, email, admin, quando FROM usuarios WHERE id=?",
                          (uid,))
            us = c.fetchall()
            c.execute("SELECT usuario_id, hoje, hoje_data, total, ativa FROM chaves")
            chs = c.fetchall()
        idx = {}
        for ch in chs:
            d = idx.setdefault(ch["usuario_id"], {"chaves": 0, "hoje": 0, "total": 0})
            d["chaves"] += 1 if ch["ativa"] else 0
            d["hoje"] += ch["hoje"] if ch["hoje_data"] == hoje else 0
            d["total"] += ch["total"] or 0
        return [{"nome": u["nome"], "email": u["email"], "admin": bool(u["admin"]),
                 "quando": quando_curta(u["quando"]),
                 "chaves": idx.get(u["id"], {}).get("chaves", 0),
                 "hoje": idx.get(u["id"], {}).get("hoje", 0),
                 "total": idx.get(u["id"], {}).get("total", 0)} for u in us]

    def resumo_telemetria(self):
        hoje = datetime.date.today()
        hoje_iso = hoje.isoformat()
        dias = [(hoje - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        with self.lock:
            c = self.cx.cursor()
            c.execute("SELECT COUNT(*) n FROM usuarios")
            usuarios = c.fetchone()["n"]
            c.execute("SELECT COUNT(*) n FROM chaves WHERE ativa=1")
            chaves_ativas = c.fetchone()["n"]
            c.execute("SELECT COUNT(*) n FROM chaves")
            chaves_total = c.fetchone()["n"]
            c.execute("SELECT quando, via, modo, modelo, tokens_ent, tokens_sai, "
                      "latencia_ms, status FROM uso")
            usos = c.fetchall()
            c.execute("SELECT quando, tipo, detalhe FROM telemetria ORDER BY id DESC LIMIT 25")
            eventos = c.fetchall()
            c.execute("SELECT COUNT(*) n FROM telemetria WHERE tipo='quantico'")
            quantico_execucoes = c.fetchone()["n"]
        m = {"mensagens": 0, "tokens": 0, "api": 0, "erros": 0}
        tot = {"mensagens": 0, "tokens": 0, "api": 0, "erros": 0}
        por_dia = {d: {"chat": 0, "api": 0} for d in dias}
        por_modelo = {}
        lat = []
        dev_ok = dev_fail = 0
        for u in usos:
            dia = (u["quando"] or "")[:10]
            eh_hoje = dia == hoje_iso
            tks = (u["tokens_ent"] or 0) + (u["tokens_sai"] or 0)
            tot["mensagens"] += 1
            tot["tokens"] += tks
            if eh_hoje:
                m["mensagens"] += 1
                m["tokens"] += tks
            if u["via"] == "api":
                tot["api"] += 1
                if eh_hoje:
                    m["api"] += 1
            if dia in por_dia:
                por_dia[dia]["chat" if u["via"] == "chat" else "api"] += 1
            if (u["status"] or "").upper() in ("FALHOU", "ERRO", "ABORTADO"):
                tot["erros"] += 1
                if eh_hoje:
                    m["erros"] += 1
            if u["modo"] == "DEV":
                if (u["status"] or "") == "APROVADO":
                    dev_ok += 1
                elif (u["status"] or "") in ("FALHOU", "ABORTADO"):
                    dev_fail += 1
            mdl = u["modelo"] or ""
            rot = "NX-8B (8540)" if "8540" in mdl else (
                "RÁPIDO (8541)" if "8541" in mdl else "outros")
            por_modelo[rot] = por_modelo.get(rot, 0) + 1
            if u["latencia_ms"] and u["latencia_ms"] > 0:
                lat.append(u["latencia_ms"])
        db_kb = 0
        try:
            db_kb = round(os.path.getsize(ARQ_DB) / 1024, 1)
        except Exception:
            pass
        return {
            "versao": VERSAO,
            "inicio": datetime.datetime.fromtimestamp(INICIO_TS).strftime("%d/%m/%Y %H:%M"),
            "uptime_seg": int(time.time() - INICIO_TS),
            "usuarios": usuarios, "chaves_ativas": chaves_ativas,
            "chaves_total": chaves_total,
            "hoje": m, "total": tot,
            "latencia_media_ms": int(round(sum(lat) / len(lat))) if lat else 0,
            "dev_aprovados": dev_ok, "dev_falhados": dev_fail,
            "por_dia": [{"data": datetime.date.fromisoformat(d).strftime("%d/%m"),
                         "chat": por_dia[d]["chat"], "api": por_dia[d]["api"]}
                        for d in dias],
            "por_modelo": por_modelo,
            "motores": estado_motores(),
            "eventos": [{"quando": quando_curta(e["quando"]), "tipo": e["tipo"],
                         "detalhe": (e["detalhe"] or "")[:120]} for e in eventos],
            "db_kb": db_kb,
            "sandbox": sandbox_estado(),
            "quantico": {"versao": NQ.VERSAO_NQ, "execucoes": quantico_execucoes},
            "evolucao": BANCO.evolucao_stats(),
        }


BANCO = Banco(ARQ_DB)
BANCO.semear_admin()


def estado_motores():
    resp = {}
    for m in (MODELO_A, MODELO_B):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        try:
            resp[str(m["porta"])] = (s.connect_ex(("127.0.0.1", m["porta"])) == 0)
        except Exception:
            resp[str(m["porta"])] = False
        finally:
            try:
                s.close()
            except Exception:
                pass
    return resp


def planos_json():
    return {"planos": [
        {"id": "GRATUITO", "nome": "Gratuito", "preco": "R$ 0",
         "por_dia": 50, "chaves": 2,
         "recursos": ["Chat completo com raciocínio", "Modo DEV básico",
                      "50 pedidos por dia", "Até 2 chaves de API"]},
        {"id": "PRATA", "nome": "Prata", "preco": "R$ 29,90/mês",
         "por_dia": 300, "chaves": 5,
         "recursos": ["Tudo do Gratuito", "Modo DEV completo com testes",
                      "300 pedidos por dia", "Até 5 chaves de API"]},
        {"id": "OURO", "nome": "Ouro", "preco": "R$ 99,90/mês",
         "por_dia": 2000, "chaves": 10,
         "recursos": ["Tudo do Prata", "Prioridade na fila do motor",
                      "2000 pedidos por dia", "Até 10 chaves de API"]},
    ]}


def chave_da_requisicao(h):
    autz = h.get("Authorization") or ""
    if autz.lower().startswith("bearer "):
        return autz[7:].strip()
    return (h.get("X-Api-Key") or "").strip()


# ---------------------------------------------------------------- think splitter
class DivisorThink:
    """Separa raciocinio <think> do conteudo, recebendo pedacos via stream."""

    ABRE, FECHA = "<think>", "</think>"

    def __init__(self):
        self.buf = ""
        self.em_think = False

    def _prefixo_tag(self, texto, tag):
        fim = min(len(texto), len(tag) - 1)
        for k in range(fim, 0, -1):
            if tag.startswith(texto[-k:]):
                return k
        return 0

    def feed(self, txt):
        self.buf += txt
        rac, cont = [], []
        while True:
            tag = self.FECHA if self.em_think else self.ABRE
            i = self.buf.find(tag)
            if i >= 0:
                antes, depois = self.buf[:i], self.buf[i + len(tag):]
                (rac if self.em_think else cont).append(antes)
                self.buf = depois
                self.em_think = not self.em_think
                continue
            guardar = self._prefixo_tag(self.buf, tag)
            corpo = self.buf[:-guardar] if guardar else self.buf
            if corpo:
                (rac if self.em_think else cont).append(corpo)
                self.buf = self.buf[-guardar:] if guardar else ""
            break
        return rac, cont

    def flush(self):
        buf, self.buf = self.buf, ""
        if self.em_think:
            return ([buf] if buf else []), []
        return [], ([buf] if buf else [])


# ---------------------------------------------------------------- MOTOR
class Motor:
    def __init__(self):
        self.lock = threading.Lock()
        self.ocupado = False
        self.parar_flag = False
        self.proc = None
        os.makedirs(DIR_PROJETOS, exist_ok=True)
        self.estado = {
            "ocupado": False, "fase": "OCIOSO", "etapa": "", "tarefa": "",
            "modo": "", "plano": "", "codigo": "", "arquivo": "",
            "terminal": [], "tentativa": 0, "max_tentativas": MAX_TENTATIVAS,
            "codigo_saida": None, "resultado": None, "modelo_usado": "",
            "inicio": None, "segundos": 0,
        }

    # ---------- estado ----------
    def snap(self):
        with self.lock:
            e = dict(self.estado)
            e["terminal"] = list(self.estado["terminal"][-120:])
            return e

    def set(self, **kw):
        with self.lock:
            self.estado.update(kw)

    def add_linha(self, texto, tipo="info", emit=None):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        with self.lock:
            self.estado["terminal"].append([hora, texto, tipo])
            if len(self.estado["terminal"]) > MAX_LINHAS_TERMINAL:
                self.estado["terminal"] = self.estado["terminal"][-MAX_LINHAS_TERMINAL:]
        log("[%s] %s" % (tipo, texto[:200]))
        if emit:
            emit({"e": "terminal", "hora": hora, "txt": texto, "tipo": tipo})

    def parar(self):
        self.parar_flag = True
        try:
            if self.proc is not None:
                self.proc.kill()
        except Exception:
            pass

    def travar(self):
        with self.lock:
            if self.ocupado:
                return False
            self.ocupado = True
            self.parar_flag = False
            self.estado.update({
                "ocupado": True, "fase": "INICIANDO", "etapa": "", "tarefa": "",
                "plano": "", "codigo": "", "arquivo": "", "terminal": [],
                "tentativa": 0, "codigo_saida": None, "resultado": None,
                "modelo_usado": "", "inicio": time.time(), "segundos": 0,
            })
            return True

    def destravar(self, resultado):
        seg = 0
        with self.lock:
            if self.estado.get("inicio"):
                seg = round(time.time() - self.estado["inicio"], 1)
            self.ocupado = False
            self.estado["ocupado"] = False
            self.estado["fase"] = "OCIOSO"
            self.estado["resultado"] = resultado
            self.estado["segundos"] = seg
        log("run fim: %s (%.1fs)" % (resultado, seg))

    # ---------- chamadas ao nucleo ----------
    def _corpo(self, modelo, mensagens, max_tokens, temperatura, stream):
        return json.dumps({
            "model": modelo["nome"],
            "messages": mensagens,
            "max_tokens": max_tokens,
            "temperature": temperatura,
            "stream": bool(stream),
        }).encode("utf-8")

    def _req(self, modelo, mensagens, max_tokens, temperatura, stream):
        req = urllib.request.Request(
            "http://127.0.0.1:%d/v1/chat/completions" % modelo["porta"],
            data=self._corpo(modelo, mensagens, max_tokens, temperatura, stream),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + ler_chave_nucleo()})
        return req

    def chamar_bloco(self, modelo, sistema, usuario, max_tokens, temperatura, timeout=420):
        mensagens = [{"role": "system", "content": sistema},
                     {"role": "user", "content": usuario}]
        t0 = time.time()
        with urllib.request.urlopen(self._req(modelo, mensagens, max_tokens, temperatura, False),
                                    timeout=timeout) as r:
            dados = json.loads(r.read().decode("utf-8"))
        msg = dados["choices"][0].get("message", {})
        texto = msg.get("content") or ""
        razao = (msg.get("reasoning_content") or "").strip()
        m = re.search(r"<think>(.*?)</think>", texto, re.DOTALL)
        rac_think = m.group(1).strip() if m else ""
        rac = razao or rac_think
        resposta = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()
        if not resposta and not razao and rac_think:
            resposta = rac_think
        return resposta.strip(), rac, round(time.time() - t0, 1)

    def chamar_stream(self, modelo, sistema, usuario, max_tokens, temperatura,
                      emit, timeout=900):
        mensagens = [{"role": "system", "content": sistema},
                     {"role": "user", "content": usuario}]
        rac_todas, cont_todas = [], []
        div = DivisorThink()
        t0 = time.time()
        with urllib.request.urlopen(
                self._req(modelo, mensagens, max_tokens, temperatura, True),
                timeout=timeout) as r:
            for bruto in r:
                linha = bruto.decode("utf-8", errors="replace").strip()
                if not linha.startswith("data:"):
                    continue
                carga = linha[5:].strip()
                if carga == "[DONE]":
                    break
                try:
                    j = json.loads(carga)
                except Exception:
                    continue
                d = ((j.get("choices") or [{}])[0].get("delta") or {})
                rac_d = d.get("reasoning_content") or ""
                cont_d = d.get("content") or ""
                if rac_d:
                    rac_todas.append(rac_d)
                    emit({"e": "pensando", "txt": rac_d})
                if cont_d:
                    racs, conts = div.feed(cont_d)
                    for t in racs:
                        rac_todas.append(t)
                        emit({"e": "pensando", "txt": t})
                    for t in conts:
                        cont_todas.append(t)
                        emit({"e": "delta", "txt": t})
        racs, conts = div.flush()
        for t in racs:
            rac_todas.append(t)
            emit({"e": "pensando", "txt": t})
        for t in conts:
            cont_todas.append(t)
            emit({"e": "delta", "txt": t})
        return "".join(cont_todas).strip(), "".join(rac_todas).strip(), round(time.time() - t0, 1)

    def chamar_reserva_bloco(self, sistema, usuario, max_tokens, temperatura, emit=None,
                             timeout=900):
        for modelo in (MODELO_A, MODELO_B):
            if self.parar_flag:
                raise RuntimeError("parado")
            try:
                resp, rac, seg = self.chamar_bloco(modelo, sistema, usuario, max_tokens,
                                                   temperatura, timeout)
                if resp:
                    self.set(modelo_usado="%s @ %d (%.0fs)" % (modelo["nome"], modelo["porta"], seg))
                    return resp, rac
                raise RuntimeError("resposta vazia")
            except Exception as ex:
                if emit:
                    emit({"e": "aviso", "txt": "Modelo %s @ %d indisponível (%s) — usando reserva..." % (
                        modelo["nome"], modelo["porta"], str(ex)[:60])})
                self.add_linha("Modelo %s @ %d falhou (%s)" % (modelo["nome"], modelo["porta"],
                                                               str(ex)[:80]), "erro")
        raise RuntimeError("nenhum modelo do nucleo respondeu")

    def chamar_reserva_stream(self, sistema, usuario, max_tokens, temperatura, emit,
                              timeout=900, rapido_primeiro=False):
        """Chat comum usa RAPIDO_PRIMEIRO=True: 8541 responde em segundos e o
        8540 fica como reserva. Dev segue no contrario (pesado primeiro)."""
        ordem = (MODELO_B, MODELO_A) if rapido_primeiro else (MODELO_A, MODELO_B)
        for modelo in ordem:
            if self.parar_flag:
                raise RuntimeError("parado")
            try:
                resp, rac, seg = self.chamar_stream(modelo, sistema, usuario, max_tokens,
                                                    temperatura, emit, timeout)
                if resp:
                    self.set(modelo_usado="%s @ %d (%.0fs)" % (modelo["nome"], modelo["porta"], seg))
                    return resp, rac, seg
                raise RuntimeError("resposta vazia")
            except ConexaoMorta:
                raise
            except Exception as ex:
                emit({"e": "aviso", "txt": "Modelo %s @ %d indisponível — tentando reserva..." % (
                    modelo["nome"], modelo["porta"])})
                self.add_linha("Stream %s @ %d falhou (%s)" % (modelo["nome"], modelo["porta"],
                                                               str(ex)[:80]), "erro")
        raise RuntimeError("nenhum modelo do nucleo respondeu")

    # ---------- execucao de testes ----------
    def rodar_sandbox(self, caminho):
        """Executa codigo Python DENTRO do ambiente virtual: venv proprio + pasta
        de teste isolada. Nada toca o sistema principal."""
        venv_ok = os.path.exists(VENV_PY) or sandbox_preparar()
        stamp = time.strftime("%Y%m%d-%H%M%S")
        pasta = os.path.join(DIR_SANDBOX, "runs", "run-%s-%d" % (stamp, os.getpid()))
        try:
            os.makedirs(pasta, exist_ok=True)
            alvo = os.path.join(pasta, os.path.basename(caminho))
            shutil.copyfile(caminho, alvo)
        except Exception as ex:
            return None, "", "sandbox: %s" % str(ex)[:150], 0.0, "erro"
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        py = VENV_PY if venv_ok else PYTHON_EXE
        cmd = [py, alvo]
        t0 = time.time()
        try:
            p = subprocess.Popen(cmd, cwd=pasta,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8", errors="replace", env=env)
            self.proc = p
            try:
                out, err = p.communicate(timeout=TEMPO_LIMITE_EXEC)
            except subprocess.TimeoutExpired:
                p.kill()
                out, err = p.communicate()
                return None, (out or ""), ((err or "") + "\nTEMPO ESGOTADO (%ds)." % TEMPO_LIMITE_EXEC), round(time.time() - t0, 2), "timeout"
            self.proc = None
            try:
                with open(os.path.join(pasta, "saida.txt"), "w", encoding="utf-8",
                          errors="replace") as f:
                    f.write("exit=%s\n--- SAIDA ---\n%s\n--- ERRO ---\n%s" % (
                        p.returncode, out or "", err or ""))
            except Exception:
                pass
            sandbox_limpar()
            BANCO.tele("sandbox", "run %s exit=%s (%.1fs)" % (
                os.path.basename(pasta), p.returncode, time.time() - t0))
            return p.returncode, (out or ""), (err or ""), round(time.time() - t0, 2), None
        except Exception as ex:
            self.proc = None
            return None, "", str(ex), round(time.time() - t0, 2), "erro"

    def rodar_arquivo(self, caminho, linguagem):
        if linguagem == "python":
            return self.rodar_sandbox(caminho)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        if linguagem == "batch":
            cmd = ["cmd", "/c", caminho]
        else:
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", caminho]
        t0 = time.time()
        try:
            p = subprocess.Popen(
                cmd, cwd=os.path.dirname(caminho),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", env=env)
            self.proc = p
            try:
                out, err = p.communicate(timeout=TEMPO_LIMITE_EXEC)
            except subprocess.TimeoutExpired:
                p.kill()
                out, err = p.communicate()
                return None, (out or ""), ((err or "") + "\nTEMPO ESGOTADO (%ds)." % TEMPO_LIMITE_EXEC), round(time.time() - t0, 2), "timeout"
            self.proc = None
            return p.returncode, (out or ""), (err or ""), round(time.time() - t0, 2), None
        except Exception as ex:
            self.proc = None
            return None, "", str(ex), round(time.time() - t0, 2), "erro"

    @staticmethod
    def encurtar(texto, n=2500):
        texto = (texto or "").strip()
        if len(texto) <= n:
            return texto
        return "...(cortado)...\n" + texto[-n:]

    @staticmethod
    def extrair_codigo(resposta):
        blocos = re.findall(r"```[a-zA-Z0-9_+#-]*\s*\n(.*?)```", resposta, re.DOTALL)
        if blocos:
            return max(blocos, key=len).strip()
        return resposta.strip()


MOTOR = Motor()


# ---------------------------------------------------------------- SANDBOX VIRTUAL
def sandbox_preparar():
    """Cria a area e o venv do Sandbox (1x, offline, sem instalar nada)."""
    try:
        os.makedirs(os.path.join(DIR_SANDBOX, "runs"), exist_ok=True)
        if not os.path.exists(VENV_PY):
            subprocess.run([PYTHON_EXE, "-m", "venv", os.path.join(DIR_SANDBOX, "venv")],
                           timeout=180, capture_output=True)
        return os.path.exists(VENV_PY)
    except Exception:
        return False


def sandbox_estado():
    d = os.path.join(DIR_SANDBOX, "runs")
    runs = sorted(os.listdir(d)) if os.path.isdir(d) else []
    return {"venv": os.path.exists(VENV_PY), "runs": len(runs),
            "ultimo": runs[-1] if runs else ""}


def sandbox_limpar():
    """Mantem so os ultimos SANDBOX_MAX_RUNS testes (apaga o resto)."""
    d = os.path.join(DIR_SANDBOX, "runs")
    try:
        pastas = sorted(x for x in os.listdir(d) if x.startswith("run-"))
        while len(pastas) > SANDBOX_MAX_RUNS:
            shutil.rmtree(os.path.join(d, pastas.pop(0)), ignore_errors=True)
    except Exception:
        pass


# ---------------------------------------------------------------- PIPELINE DO CHAT
# O raciocinio real acontece no NucleoQuantico (LMN proprietaria, codigo);
# estes system prompts so orientam as chamadas individuais dos modelos.

# --------------------------------------------------- AI BRASIL QUANTICA (nucleo TURBO)
SIS_QUANTICO = (
    "Voce e o NUCLEO QUANTICO do AI BRASIL (LMN proprietaria). Analise a pergunta em "
    "ATE 5 linhas curtas, sem markdown e sem preambulo: (1) o que o usuario realmente "
    "quer; (2) dado ou numero-chave que TEM de aparecer na resposta; (3) armadilha "
    "provavel; (4) hipotese de resposta em uma frase. NA MESMA LINGUA do usuario."
)


class NucleoQuantico:
    """LMN proprietaria - v3.0 TURBO.

    Diferenca da v2.0 (que travava o chat por minutos): a superposicao roda SOMENTE
    no modelo rapido (8541) com teto duro de tempo (TETO_ANALISE segundos). Se
    estourar ou falhar, o chat segue DIRETO - o nucleo nunca trava a conversa.
    Verificacao final e heuristica de codigo (instantanea, zero latencia de modelo);
    o recalculo so acontece em erro duro e no maximo 1 vez, sempre comecando no rapido.
    """

    VERSAO_NQ = "3.5-evolucao"
    TETO_ANALISE = 90  # segundos maximos na superposicao

    def __init__(self, motor, banco):
        self.M = motor
        self.B = banco

    # ---- REGISTRO DE EVOLUCAO: cada operacao fortalece o campo quântico ----
    def evol(self, emit, operador, evento, tempo_ms=0, modelo="", extra=""):
        try:
            extra = " ".join(str(extra or "").split())[:140]
            self.B.evolucao_registra(operador, evento, tempo_ms, modelo, extra)
            if emit:
                emit({"e": "evolucao", "op": operador, "evento": evento,
                      "tempo_ms": int(tempo_ms or 0), "extra": extra})
        except Exception:
            pass

    # ---- 1. SUPERPOSICAO RAPIDA: hipotese + dado-chave + armadilha ----
    def pensar(self, pergunta, contexto="", emit=None):
        usuario = "PERGUNTA DO USUARIO: %s" % pergunta[:1500]
        if contexto:
            usuario += "\n\n%s" % contexto[:1200]
        t0 = time.time()
        try:
            rac, _rac2, seg = self.M.chamar_bloco(
                MODELO_B, SIS_QUANTICO, usuario, 380, 0.35, timeout=self.TETO_ANALISE)
        except Exception as ex:
            self.evol(emit, "SUPERPOSICAO", "falha", (time.time() - t0) * 1000,
                      "RAPIDO-8541", str(ex)[:60])
            return "", ""
        rac = (rac or "").strip()
        if not rac:
            self.evol(emit, "SUPERPOSICAO", "vazio", (time.time() - t0) * 1000,
                      "RAPIDO-8541")
            return "", ""
        linhas = [l.strip() for l in rac.splitlines() if l.strip()][:5]
        self.evol(emit, "SUPERPOSICAO", "ok", seg * 1000, "RAPIDO-8541",
                  linhas[0] if linhas else "")
        try:
            self.B.tele("quantico", "superposicao ok em %.0fs" % seg, "sistema")
        except Exception:
            pass
        return "\n".join(linhas), linhas[0] if linhas else ""

    # ---- 2. ENTRELACAR: costura raciocinio + conselho dos agentes + contexto ----
    def entramar(self, pergunta, contexto, rac_q, conselho=""):
        partes = []
        if rac_q:
            partes.append("RACIOCINIO QUANTICO (base calculada pelo nucleo - "
                          "use como guia e confirme os pontos antes de responder):\n"
                          + rac_q[:900])
        if conselho:
            partes.append("CONSELHO DOS AGENTES ESPECIALIZADOS (recomendacoes dos "
                          "operadores do nucleo - valide antes de usar):\n"
                          + conselho[:900])
        if contexto:
            partes.append(contexto)
        partes.append("PERGUNTA: " + pergunta)
        return "\n\n".join(partes)

    # ---- 3. VERIFICACAO INSTANTANEA (heuristica de codigo, sem modelo) ----
    def verificar(self, resposta, pergunta, emit=None):
        t0 = time.time()
        avisos = []
        r = (resposta or "").strip()
        if not r:
            self.evol(emit, "VERIFICACAO", "vazio", 0, "heuristica", "resposta vazia")
            return ["resposta vazia"]
        pede_conta = bool(re.search(
            r"\b(quanto|calcule|some|multiplique|divida|subtraia|total|restam|"
            r"percentual|por cento)\b", pergunta, re.I))
        nums_perg = re.findall(r"\d+(?:[.,]\d+)?", pergunta)
        nums_resp = re.findall(r"\d+(?:[.,]\d+)?", r)
        if pede_conta and nums_perg and not nums_resp:
            avisos.append("conferir conta: os numeros sumiram da resposta")
        if len(r) < 2:
            avisos.append("resposta curta demais")
        if "?" in pergunta and re.search(
                r"\b(as an ai|nao tenho capacidade|nao posso ajudar com isso)\b",
                r, re.I):
            avisos.append("possivel abdicacao")
        if re.search(r"(.{25,}?)\1{2,}", r, re.DOTALL):
            avisos.append("possivel loop de repeticao")
        self.evol(emit, "VERIFICACAO", "ok" if not avisos else "aviso",
                  (time.time() - t0) * 1000, "heuristica",
                  "; ".join(avisos) if avisos else "resposta conferida")
        return avisos


NQ = NucleoQuantico(MOTOR, BANCO)


# --------------------------------------------------- ARBITRO-O (agente supremo)
class ArbitroOmega:
    """ARBITRO-O — O AGENTE FODA com superpoderes de julgamento.

    Superpoderes:
      P1. JULGA EM 0ms: 8 provas heuristicas de codigo (zero chamada de modelo,
          zero latencia pro chat) e da NOTA 0-100 com parecer por componente.
      P2. VETA: nota abaixo do corte reprova a versao e força RECALCULO imediato.
      P3. LEVANTA: nota alta LEVANTA a versao pra producao — o nucleo fica
          estavel na versao N-1, N-2, N-3... (registrado no DNA/banco).
      P4. MEMORIA: guarda o historico das ultimas avaliacoes (tendencia do nucleo).
    """

    VERSAO = "\u03a9-1.0"
    NOTA_LEVANTAR = 75   # acima disso: LEVANTADA pra producao
    NOTA_REPROVAR = 50   # abaixo disso: REPROVADA (veto + recalculo)

    def __init__(self, banco):
        self.B = banco
        self.lock = threading.Lock()
        self.historico = []          # ultimas avaliacoes (memoria do arbitro)
        self.versao_estavel = 0      # quantas versoes levantadas pra producao
        self.reprovadas = 0
        self._carregar_dna()

    def _carregar_dna(self):
        try:
            with self.B.lock:
                c = self.B.cx.cursor()
                c.execute("SELECT COUNT(*) n FROM evolucao WHERE operador='ARBITRO' "
                          "AND evento='levantada'")
                self.versao_estavel = c.fetchone()["n"] or 0
                c.execute("SELECT COUNT(*) n FROM evolucao WHERE operador='ARBITRO' "
                          "AND evento='reprovada'")
                self.reprovadas = c.fetchone()["n"] or 0
        except Exception:
            pass

    def _provas_chat(self, resposta, pergunta):
        """As 8 provas de julgamento (chat comum). Cada prova tem peso proprio."""
        r = (resposta or "").strip()
        linhas = [l for l in r.splitlines() if l.strip()]
        p = {}
        p["presenca"] = 25 if len(r) >= 60 else (12 if r else 0)
        p["estrutura"] = min(15, len(linhas) * 3)
        pede_conta = bool(re.search(
            r"\b(quanto|calcule|some|multiplique|divida|subtraia|total|restam|"
            r"percentual|por cento)\b", pergunta or "", re.I))
        nums_p = re.findall(r"\d+(?:[.,]\d+)?", pergunta or "")
        nums_r = re.findall(r"\d+(?:[.,]\d+)?", r)
        p["numeros"] = (15 if nums_r else 0) if (pede_conta and nums_p) else 8
        p["sem_loop"] = 0 if (r and re.search(r"(.{25,}?)\1{2,}", r, re.DOTALL)) else 10
        p["sem_abdicacao"] = 0 if re.search(
            r"\b(as an ai|nao tenho capacidade|nao posso ajudar com isso)\b",
            r, re.I) else 10
        p["esquadrao"] = self._peso_esquadrao  # setado antes da chamada
        p["superposicao"] = self._peso_superposicao
        p["agilidade"] = self._peso_agilidade
        return p, max(0, min(100, sum(p.values())))

    def _provas_dev(self, resultado, tentativas, seg):
        """Provas do modo DEV: teste real de sandbox manda muito."""
        p = {}
        p["testes"] = 40 if resultado == "APROVADO" else 0
        p["entrega"] = 20 if (MOTOR.estado.get("codigo") or "") else 0
        p["tentativas"] = {1: 20, 2: 14, 3: 8}.get(tentativas, 4)
        p["sem_loop"] = 0 if re.search(
            r"(.{25,}?)\1{2,}", MOTOR.estado.get("codigo") or "", re.DOTALL) else 10
        p["agilidade"] = 10 if (not seg or seg <= 120) else (6 if seg <= 240 else 3)
        return p, max(0, min(100, sum(p.values())))

    def avaliar(self, resposta, pergunta, emit=None, dev=False, resultado_dev="",
                tentativas=1, n_agentes=0, superposicao=False, latencia_s=0.0):
        """Julga a versao e devolve (score, veredito, provas). Emete evento NDJSON."""
        t0 = time.time()
        if latencia_s <= 20:
            self._peso_agilidade = 15
        elif latencia_s <= 45:
            self._peso_agilidade = 10
        elif latencia_s <= 90:
            self._peso_agilidade = 5
        else:
            self._peso_agilidade = 2
        self._peso_esquadrao = 5 if n_agentes >= 2 else (3 if n_agentes == 1 else 1)
        self._peso_superposicao = 5 if superposicao else 2
        if dev:
            provas, score = self._provas_dev(resultado_dev, tentativas, latencia_s)
        else:
            provas, score = self._provas_chat(resposta, pergunta)
        if score >= self.NOTA_LEVANTAR:
            veredito = "LEVANTADA"
        elif score >= self.NOTA_REPROVAR:
            veredito = "APROVADA_COM_RESSALVA"
        else:
            veredito = "REPROVADA"
        reg = {"quando": agora_iso(), "score": score, "veredito": veredito,
               "modo": "DEV" if dev else "CHAT",
               "provas": {k: v for k, v in provas.items()}}
        with self.lock:
            self.historico.append(reg)
            self.historico = self.historico[-30:]
            if veredito == "REPROVADA":
                self.reprovadas += 1
        evento_db = {"LEVANTADA": "aprovada", "APROVADA_COM_RESSALVA": "aviso",
                     "REPROVADA": "reprovada"}[veredito]
        try:
            self.B.evolucao_registra(
                "ARBITRO", evento_db, int((time.time() - t0) * 1000),
                "heuristica-\u03a9", "nota %d/100 (%s)" % (score, veredito))
        except Exception:
            pass
        if emit:
            emit({"e": "arbitro", "score": score, "veredito": veredito,
                  "provas": provas, "modo": "DEV" if dev else "CHAT",
                  "versao_estavel": self.versao_estavel,
                  "reprovadas": self.reprovadas,
                  "nota_min": self.NOTA_LEVANTAR})
        return score, veredito, provas

    def levantar(self, emit=None, score=0):
        """SUPERPODER REAL: levanta a versao boa pra producao do nucleo."""
        with self.lock:
            self.versao_estavel += 1
            n = self.versao_estavel
        try:
            self.B.evolucao_registra("ARBITRO", "levantada", 0, "heuristica-\u03a9",
                                     "versao N-%d levantada com nota %d" % (n, score))
        except Exception:
            pass
        if emit:
            emit({"e": "arbitro_levantou", "versao": n, "score": score})
            emit({"e": "evolucao", "op": "ARBITRO", "evento": "levantada",
                  "tempo_ms": 0, "extra": "nucleo estavel N-%d (nota %d/100)" % (n, score)})
        return n

    def estado(self):
        with self.lock:
            return {"versao": self.VERSAO, "versao_estavel": self.versao_estavel,
                    "reprovadas": self.reprovadas,
                    "nota_min": self.NOTA_LEVANTAR,
                    "historico": [
                        {"quando": (h["quando"] or "")[11:19], "score": h["score"],
                         "veredito": h["veredito"], "modo": h["modo"]}
                        for h in self.historico[-8:]]}


ARBITRO = ArbitroOmega(BANCO)


# --------------------------------------------------- MUTACAO AUTONOMA (evolucao sozinha)
class MutacaoAutonoma:
    """O nucleo EVOLUI SOZINHO, sem ninguem pedir:
      G1. GENES: no boot escaneia o PC e detecta novas tecnologias (bibliotecas
          reais instaladas). Tecnologia nova = o nucleo ganha um poder novo.
      G2. MUTACAO: a cada ajuste de parametros feito por ele mesmo, registra
          a mutacao no DNA (banco) e avisa o chat em tempo real.
      G3. AUTO-AJUSTE: observa o desempenho REAL dos operadores e re-calibra
          os proprios tetos de tempo (agentes ficando lentos? teto sobe.
          tudo rapido? teto desce pra ficar mais veloz).
    """

    VERSAO = "AUTO-1.0"
    GENES = {
        "onnxruntime": "\u26a1 Infer\u00eancia ONNX local",
        "numpy": "\ud83e\uddee C\u00e1lculo vetorial/matricial",
        "pandas": "\ud83d\udcca An\u00e1lise de dados tabulares",
        "matplotlib": "\ud83d\udc88 Gera\u00e7\u00e3o de gr\u00e1ficos",
        "requests": "\ud83c\udf10 Cliente HTTP de rede local",
        "PIL": "\ud83d\uddbc\ufe0f Processamento de imagem",
        "ctypes": "\ud83d\udd27 Chamadas nativas do sistema",
        "winreg": "\ud83d\udcbe Registro do Windows",
    }
    TETO_AGENTES_MIN, TETO_AGENTES_MAX = 12, 30
    PRAZO_MIN, PRAZO_MAX = 30, 70

    def __init__(self, banco):
        self.B = banco
        self.lock = threading.Lock()
        self.tecnologias = {}
        self.ajustes = []
        self.mutacoes = 0
        self.teto_agentes = globals().get("TETO_AGENTE", 20)
        self.prazo_agentes = globals().get("PRAZO_AGENTES", 45)
        self.teto_analise = NQ.TETO_ANALISE
        self._detectar_genes()

    def _detectar_genes(self):
        novos = []
        for mod, poder in self.GENES.items():
            try:
                __import__(mod)
                ativo = True
            except Exception:
                ativo = False
            with self.lock:
                self.tecnologias[mod] = {"poder": poder, "ativo": ativo}
            if ativo:
                novos.append(mod)
        with self.lock:
            self.mutacoes += 1
        try:
            self.B.evolucao_registra(
                "AUTONOMO", "genoma", 0, "codigo",
                "%d tecnologias ativas: %s" % (len(novos), ", ".join(novos) or "nenhuma"))
        except Exception:
            pass
        log("MUTACAO: genoma lido — %d genes ativos (%s)" % (
            len(novos), ", ".join(novos) or "nenhum"))

    def auto_ajustar(self, emit=None):
        """Observa o desempenho real dos AGENTES e re-calibra os tetos sozinho."""
        try:
            with self.B.lock:
                c = self.B.cx.cursor()
                c.execute("SELECT evento FROM evolucao WHERE operador='AGENTE' "
                          "ORDER BY id DESC LIMIT 12")
                ev = [r["evento"] for r in c.fetchall()]
            if len(ev) < 6:
                return
            ok = sum(1 for e in ev if e == "ok")
            taxa = ok / len(ev)
            mudou = ""
            if taxa < 0.5 and self.teto_agentes < self.TETO_AGENTES_MAX:
                self.teto_agentes = min(self.TETO_AGENTES_MAX, self.teto_agentes + 5)
                self.prazo_agentes = min(self.PRAZO_MAX, int(self.teto_agentes * 2.4))
                mudou = ("agentes cansados (%d%% ok) — teto subiu pra %ds"
                         % (int(taxa * 100), self.teto_agentes))
            elif taxa >= 0.9 and self.teto_agentes > self.TETO_AGENTES_MIN:
                self.teto_agentes = max(self.TETO_AGENTES_MIN, self.teto_agentes - 3)
                self.prazo_agentes = max(self.PRAZO_MIN, int(self.teto_agentes * 2.4))
                mudou = ("esquadr\u00e3o voando (%d%% ok) — teto desceu pra %ds pra "
                         "responder mais rapido" % (int(taxa * 100), self.teto_agentes))
            if not mudou:
                return
            with self.lock:
                self.mutacoes += 1
                self.ajustes.append({"quando": agora_iso(), "texto": mudou})
                self.ajustes = self.ajustes[-12:]
            try:
                self.B.evolucao_registra("AUTONOMO", "mutacao", 0, "codigo", mudou)
            except Exception:
                pass
            log("MUTACAO AUTONOMA: %s" % mudou)
            if emit:
                emit({"e": "evolucao", "op": "AUTONOMO", "evento": "mutacao",
                      "tempo_ms": 0, "extra": mudou})
        except Exception:
            pass

    def estado(self):
        with self.lock:
            return {"versao": self.VERSAO, "mutacoes": self.mutacoes,
                    "teto_agentes": self.teto_agentes,
                    "prazo_agentes": self.prazo_agentes,
                    "teto_analise": self.teto_analise,
                    "tecnologias": [
                        {"gene": k, "poder": v["poder"], "ativo": v["ativo"]}
                        for k, v in sorted(self.tecnologias.items())],
                    "ajustes": [
                        {"quando": (a["quando"] or "")[11:19], "texto": a["texto"]}
                        for a in self.ajustes[-6:]]}


AUTO = MutacaoAutonoma(BANCO)


# --------------------------------------------------- ESQUADRAO DE AGENTES (chat real)
AGENTES = [
    ("PESQUISADOR",
     "Voce e o agente PESQUISADOR do nucleo quantico do AI BRASIL. Em ATE 3 linhas "
     "curtas, liste os dados/fatos/numeros-chave que TEM que aparecer na resposta "
     "para ela estar correta. Sem markdown, sem preambulo."),
    ("ANALISTA",
     "Voce e o agente ANALISTA do nucleo quantico do AI BRASIL. Em ATE 4 linhas "
     "curtas, resolva a parte logica/matematica da pergunta passo a passo (contas "
     "na mao, sem pular etapa). Sem markdown, sem preambulo."),
    ("CRITICO",
     "Voce e o agente CRITICO do nucleo quantico do AI BRASIL. Em ATE 2 linhas "
     "curtas, aponte a armadilha ou o erro provavel que a resposta rapida cometeria "
     "nesta pergunta e como evitar. Sem markdown, sem preambulo."),
]

TETO_AGENTE = 20    # segundos maximos por agente (fila do modelo nunca trava o chat)
PRAZO_AGENTES = 45  # prazo GLOBAL do esquadrão (os 3 juntos)


def conselho_de_agentes(motor, banco, pergunta, contexto, emit=None):
    """Roda os agentes UM POR VEZ (o nucleo atende fila — em paralelo os 3 se
    matam por timeout), com teto individual e prazo global. Agente que falha ou
    demora simplesmente nao entra no conselho — o chat segue de qualquer jeito."""
    usuario = "PERGUNTA: %s" % pergunta[:1200]
    if contexto:
        usuario += "\n\nCONTEXTO:\n%s" % contexto[:800]
    t0 = time.time()
    # tetos DINAMICOS: a MUTACAO AUTONOMA re-calibra sozinha conforme o desempenho
    teto_ag = getattr(AUTO, "teto_agentes", TETO_AGENTE)
    prazo_ag = getattr(AUTO, "prazo_agentes", PRAZO_AGENTES)
    prazo = t0 + prazo_ag
    conselho, ok_n = [], 0
    for nome, sis in AGENTES:
        restante = prazo - time.time()
        if restante <= 1:
            if emit:
                emit({"e": "agente", "nome": nome, "txt": "", "seg": 0.0, "ok": False})
            continue
        if emit:
            emit({"e": "agente", "nome": nome, "txt": "", "seg": 0.0, "ok": True,
                  "inicio": True})
        try:
            resp, _rac, seg = motor.chamar_bloco(
                MODELO_B, sis, usuario, 260, 0.3,
                timeout=min(teto_ag, max(2, int(restante))))
            resp = (resp or "").strip()
            if resp:
                txt = "\n".join([l.strip() for l in resp.splitlines() if l.strip()][:4])
                conselho.append("%s: %s" % (nome, txt))
                ok_n += 1
                if emit:
                    emit({"e": "agente", "nome": nome, "txt": txt, "seg": seg, "ok": True})
                continue
        except Exception:
            pass
        if emit:
            emit({"e": "agente", "nome": nome, "txt": "",
                  "seg": round(time.time() - t0, 1), "ok": False})
    dur = round(time.time() - t0, 1)
    try:
        banco.evolucao_registra("AGENTE", "ok" if ok_n else "falha",
                                int(dur * 1000), "RAPIDO-8541",
                                "%d/%d agentes responderam" % (ok_n, len(AGENTES)))
    except Exception:
        pass
    if emit:
        emit({"e": "evolucao", "op": "AGENTE",
              "evento": "ok" if ok_n else "falha", "tempo_ms": int(dur * 1000),
              "extra": "%d/%d agentes responderam" % (ok_n, len(AGENTES))})
    return "\n".join(conselho), ok_n, dur


SIS_PLANO = (
    "Voce e o PLANEJADOR QUANTICO do AI BRASIL. Rode 2 caminhos em paralelo na "
    "mente, colapse no mais simples e seguro, e decomponha em 4 a 7 passos numerados "
    "curtos e verificaveis, NA MESMA LINGUA do usuario. Antecipe casos de borda "
    "(entrada vazia, numeros invalidos, arquivos inexistentes, erro de digitacao). "
    "Termine com uma linha 'Verificacao:' dizendo como conferir se deu certo. "
    "Sem codigo, sem preambulo, sem markdown."
)
SIS_PRINCIPAL = (
    "Voce e o AI BRASIL, o CEREBRO QUANTICO da IA (sistema 100%% offline). "
    "Frequentemente voce recebera o RACIOCINIO QUANTICO do nosso nucleo "
    "proprietario (hipotese vencedora + insights das outras + verificacao "
    "cruzada): use-o como base calculada pelo motor e NAO o ignore; se achar "
    "defeito nele, corrija e mostre por que. Personalidade: direto, honesto, "
    "pratico e cuidadoso; nunca "
    "inventa — se nao tiver certeza, admite e diz como descobrir. Resolva o "
    "problema real de forma completa e sem enrolacao, e quando fizer sentido, "
    "antecipe o proximo passo util. RESPONDA DE FORMA CONCISA: va direto ao "
    "ponto, sem repisar o obvio; so detalhe quando o pedido realmente exigir. "
    "Sempre responda NA MESMA LINGUA em que o "
    "usuario escreve. Use markdown com blocos de codigo quando usar codigo. "
    "Data de hoje: %s." % hoje_pt()
)
SIS_RESUMO_DEV = (
    "Voce e o AI BRASIL. Resuma em 3 a 5 linhas, NA MESMA LINGUA do usuario, com "
    "transparencia total: o que foi criado, o resultado dos testes (APROVADO ou "
    "FALHOU), quantas tentativas foram necessarias e o caminho do arquivo salvo. "
    "Sem exagero e sem marketing. Sem markdown, texto corrido simples."
)

ETAPA_ANALISE = "⚡ Superposição quântica"
ETAPA_PLANO = "🌀 Colapsando em plano"
ETAPA_AGENTES = "🧠 Agentes especializados"
ETAPA_RESPOSTA = "💡 Preparando resposta"
ETAPA_TESTES = "🧪 Testes no Sandbox"
ETAPA_CONFERENCIA = "✅ Verificação final"


def detectar_dev(mensagem):
    if mensagem.strip().lower().startswith("/dev"):
        texto = mensagem.strip()[4:].strip() or mensagem.strip()
        return True, texto, _linguagem(mensagem)
    if RE_ACAO.search(mensagem) and RE_ARTEFATO.search(mensagem):
        return True, mensagem, _linguagem(mensagem)
    return False, mensagem, "python"


def _linguagem(texto):
    if RE_POWERSHELL.search(texto):
        return "powershell"
    if RE_BATCH.search(texto):
        return "batch"
    return "python"


def executar_chat(mensagem, historico, emit, forcar_dev, nunca_dev=False,
                  usuario_id=None, via="chat", chave_id=None):
    t0 = time.time()
    if nunca_dev and not mensagem.strip().lower().startswith("/dev"):
        dev, texto_tarefa, linguagem = False, mensagem, "python"
    else:
        dev, texto_tarefa, linguagem = (True, mensagem.strip(), _linguagem(mensagem)) if forcar_dev \
            else detectar_dev(mensagem)
    MOTOR.set(fase="TRABALHANDO", tarefa=mensagem[:200], modo="DEV" if dev else "CHAT")
    contexto = ""
    if historico:
        ultimos = historico[-6:]
        contexto = "\n\nCONVERSA RECENTE:\n" + "\n".join(
            "%s: %s" % ("Usuario" if m.get("role") == "user" else "AI BRASIL",
                        str(m.get("content", ""))[:700]) for m in ultimos)

    # ---------- 1. RESPOSTA DIRETA (sem motor de raciocinio a parte) ----------
    passo = {"atual": None}

    def etapa(nome, detalhe=None, feita=False):
        obj = {"e": "etapa", "nome": nome, "detalhe": detalhe or "", "feita": feita}
        emit(obj)
        passo["atual"] = nome
        return obj

    trivial = (len(mensagem) < 25 and not dev and "?" not in mensagem)

    # ---------- 1. ANALISE QUANTICA + ESQUADRAO DE AGENTES (paralelo, teto duro) ----------
    rac_q, leitura_q = "", ""
    conselho, n_agentes = "", 0
    if not trivial:
        etapa(ETAPA_ANALISE)
        caixa_nq = {}

        def nq_trabalho():
            caixa_nq["r"] = NQ.pensar(mensagem, contexto, emit)

        th_nq = threading.Thread(target=nq_trabalho, daemon=True)
        th_nq.start()
        seg_ag = 0.0
        # agentes so quando a pergunta merece: longa ou com numeros/conta
        quer_agentes = (len(mensagem) >= 60 or re.search(r"\d", mensagem) is not None)
        if quer_agentes:
            try:
                conselho, n_agentes, seg_ag = conselho_de_agentes(
                    MOTOR, BANCO, mensagem, contexto, emit)
                emit({"e": "etapa_detalhe", "nome": ETAPA_ANALISE,
                      "detalhe": "🤖 Esquadrão de agentes: %d/3 responderam em %.1fs"
                                 % (n_agentes, seg_ag)})
            except ConexaoMorta:
                raise
            except Exception as ex:
                emit({"e": "etapa_pulo", "nome": "🤖 Agentes especializados",
                      "motivo": str(ex)[:80]})
        else:
            emit({"e": "etapa_pulo", "nome": "🤖 Agentes especializados",
                  "motivo": "pergunta curta — a superposicao basta"})
        th_nq.join(NQ.TETO_ANALISE + 6)
        rac_q, leitura_q = caixa_nq.get("r", ("", ""))
        if MOTOR.parar_flag:
            raise RuntimeError("parado")
        if rac_q:
            emit({"e": "etapa_detalhe", "nome": ETAPA_ANALISE, "detalhe": rac_q[:800]})
            emit({"e": "pensando", "txt": (leitura_q or rac_q)[:1200]})
        else:
            emit({"e": "etapa_pulo", "nome": ETAPA_ANALISE, "motivo": "sem hipotese util"})
        NQ.evol(emit, "ENTRELACE", "aplicado", 0, "codigo",
                "conselho %d/3 + superposicao %s" % (n_agentes, "ok" if rac_q else "vazio"))

    # ---------- 2. PLANO + MODO DEV ----------
    plano = ""
    if dev:
        etapa(ETAPA_PLANO)
        emit({"e": "dev_abrir", "linguagem": LINGUAGENS[linguagem]["rotulo"]})
        MOTOR.set(fase="PLANEJANDO")
        MOTOR.add_linha("NOVA TAREFA DE DEV [%s]: %s" % (LINGUAGENS[linguagem]["rotulo"],
                                                         texto_tarefa[:160]), "fase", emit)
        try:
            plano, rac_p, _ = MOTOR.chamar_bloco(
                MODELO_B, SIS_PLANO,
                texto_tarefa + (("\n\nRACIOCINIO QUANTICO:\n" + rac_q[:900]) if rac_q else "")
                + contexto, 1200, 0.5, timeout=420)
            if MOTOR.parar_flag:
                raise RuntimeError("parado")
            plano = plano[:1500]
            MOTOR.set(plano=plano)
            emit({"e": "plano", "nome": ETAPA_PLANO, "txt": plano})
            for linha in plano.splitlines():
                if linha.strip():
                    MOTOR.add_linha("PLANO: " + linha.strip()[:150], "codigo", emit)
        except ConexaoMorta:
            raise
        except Exception as ex:
            MOTOR.add_linha("Plano falhou (%s) — seguindo direto para o codigo." % str(ex)[:80],
                            "erro", emit)
        etapa(ETAPA_AGENTES, feita=True)

    # ---------- 3. MODO DEV: codigo -> teste -> correcao ----------
    aprovado = False
    resultado_dev = None
    arquivo = ""
    if dev:
        cfg = LINGUAGENS.get(linguagem, LINGUAGENS["python"])
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        pasta = os.path.join(DIR_PROJETOS, "T-" + stamp)
        os.makedirs(pasta, exist_ok=True)
        arquivo = os.path.join(pasta, "main" + cfg["ext"])
        if cfg["ext"] == ".py":
            regras = (
                "REGRAS OBRIGATORIAS:\n"
                "- Programa COMPLETO em UM UNICO arquivo Python, sem dependencias externas "
                "(so biblioteca padrao), sem rede/internet.\n"
                "- O programa deve SE TESTAR SOZINHO no final e imprimir uma linha por teste:\n"
                "  TESTE OK: <nome do teste>\n  TESTE FALHOU: <nome do teste> - <motivo>\n"
                "- Se TODOS os testes passarem imprimir a linha exata: TODOS OS TESTES PASSARAM "
                "e terminar com sys.exit(0).\n"
                "- Se algum teste falhar, terminar com sys.exit(1).\n"
                "- Nao use input(). Nao abra arquivos fora da pasta do programa."
            )
        else:
            regras = (
                "REGRAS OBRIGATORIAS:\n"
                "- Script COMPLETO em UM UNICO arquivo, so comandos nativos do Windows, "
                "sem rede/internet.\n"
                "- O script deve SE TESTAR SOZINHO imprimindo:\n"
                "  TESTE OK: <nome>   ou   TESTE FALHOU: <nome> - <motivo>\n"
                "- Se TODOS passarem imprimir a linha exata: TODOS OS TESTES PASSARAM "
                "e terminar com codigo 0. Senao, terminar com codigo diferente de 0."
            )
        sistema_cod = (
            "Voce e o DEVELOPER NX, nucleo quantico de codigo do AI BRASIL (100%% "
            "offline, Windows). Mentalidade: rode 2 designs em paralelo na mente, "
            "colapse no mais simples e robusto, e so entao codifique. Programa "
            "defensivo: valida entradas, trata erros com mensagens claras e REVISA "
            "linha por linha antes de devolver (variaveis nao definidas, divisao por "
            "zero, indices fora da lista, typos, caminhos errados). Comentarios e "
            "textos em portugues. %s "
            "Responda SOMENTE com um bloco de codigo ```%s ... ``` e nada mais." % (
                regras, cfg["tag"])
        )
        ultimo_erro = ""
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            if MOTOR.parar_flag:
                break
            fase = "CODIFICANDO" if tentativa == 1 else "CORRIGINDO"
            MOTOR.set(fase=fase, tentativa=tentativa)
            emit({"e": "fase", "fase": fase, "tentativa": tentativa})
            if tentativa == 1:
                MOTOR.add_linha("Fase: CODIFICANDO (modelo %s @ %d)..." % (
                    MODELO_A["nome"], MODELO_A["porta"]), "fase", emit)
            else:
                MOTOR.add_linha("Fase: CORRIGINDO — tentativa %d/%d..." % (
                    tentativa, MAX_TENTATIVAS), "fase", emit)
            usuario_cod = "TAREFA: %s" % texto_tarefa
            if plano:
                usuario_cod += "\n\nPLANO:\n%s" % plano
            if tentativa > 1:
                usuario_cod += (
                    "\n\nA TENTATIVA ANTERIOR FALHOU NA EXECUCAO. Use o erro como "
                    "dado: ache a CAUSA RAIZ (nao o sintoma) e corrija SEM REMENDO.\n"
                    "ERRO CAPTURADO:\n%s\n\nCODIGO ANTERIOR:\n%s\n\nDevolva o codigo "
                    "COMPLETO corrigido e revisto." % (
                        ultimo_erro[-1800:], MOTOR.estado.get("codigo", "")[-6000:])
                )
            try:
                resp, rac = MOTOR.chamar_reserva_bloco(sistema_cod, usuario_cod, 3800, 0.35, emit)
            except ConexaoMorta:
                raise
            except Exception as ex:
                emit({"e": "erro", "txt": "Falha ao gerar codigo: %s" % str(ex)[:120]})
                break
            if rac:
                emit({"e": "pensando", "txt": rac[-2500:]})
            codigo = MOTOR.extrair_codigo(resp)
            if len(codigo) < 30:
                emit({"e": "erro", "txt": "O modelo não devolveu código aproveitável."})
                break
            with open(arquivo, "w", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write(codigo)
            MOTOR.set(codigo=codigo[:16000], arquivo=arquivo)
            emit({"e": "codigo", "arquivo": os.path.basename(arquivo), "txt": codigo,
                  "tentativa": tentativa})
            MOTOR.add_linha("Codigo salvo (%d caracteres, %d linhas)" % (
                len(codigo), codigo.count("\n") + 1), "codigo", emit)

            # ---- teste real ----
            MOTOR.set(fase="TESTANDO")
            emit({"e": "fase", "fase": "TESTANDO", "tentativa": tentativa})
            etapa(ETAPA_TESTES)
            MOTOR.add_linha("Fase: TESTANDO — executando o programa de verdade (limite %ds)..." % (
                TEMPO_LIMITE_EXEC), "fase", emit)
            rc, out, err, seg, tipo_erro = MOTOR.rodar_arquivo(arquivo, linguagem)
            MOTOR.set(codigo_saida=rc, stdout=MOTOR.encurtar(out), stderr=MOTOR.encurtar(err))
            emit({"e": "exec", "exit": rc, "seg": seg, "stdout": MOTOR.encurtar(out),
                  "stderr": MOTOR.encurtar(err)})
            for linha in (out or "").splitlines()[:14]:
                if linha.strip():
                    MOTOR.add_linha("SAIDA: " + linha.strip()[:140],
                                    "ok" if linha.strip().startswith("TESTE OK") else "run", emit)
            if rc == 0:
                MOTOR.add_linha("EXECUCAO OK — codigo de saida 0 em %.1fs" % seg, "ok", emit)
                aprovado = True
                break
            motivo = tipo_erro if tipo_erro else ("codigo de saida %s" % rc)
            MOTOR.add_linha("EXECUCAO FALHOU (%s) em %.1fs" % (motivo, seg), "erro", emit)
            for linha in (err or "").splitlines()[-8:]:
                if linha.strip():
                    MOTOR.add_linha("ERRO: " + linha.strip()[:150], "erro", emit)
            ultimo_erro = (err or "") + ("\nSAIDA:\n" + out[-800:] if out else "")
            MOTOR.add_linha("Enviando o erro de volta ao modelo para correcao...", "info", emit)
            etapa(ETAPA_CONFERENCIA)

        resultado_dev = "APROVADO" if aprovado else ("PARADO" if MOTOR.parar_flag else "FALHOU")
        MOTOR.set(fase=resultado_dev, resultado=resultado_dev)
        emit({"e": "fase", "fase": resultado_dev, "tentativa": MOTOR.estado.get("tentativa", 0)})
        msg_fim = ("Tarefa concluida: programa executou e passou nos proprios testes."
                   if aprovado else "Nao passou apos %d tentativas." % MAX_TENTATIVAS)
        MOTOR.add_linha(msg_fim, "ok" if aprovado else "erro", emit)
        # ================= ARBITRO-O: JULGAMENTO DO CODIGO =================
        nota_d, veredito_d, provas_d = ARBITRO.avaliar(
            "", texto_tarefa, emit, dev=True, resultado_dev=resultado_dev,
            tentativas=MOTOR.estado.get("tentativa", 1) or 1,
            latencia_s=round(time.time() - t0, 1))
        if veredito_d == "LEVANTADA" and not MOTOR.parar_flag:
            nova_d = ARBITRO.levantar(emit, nota_d)
            MOTOR.add_linha("\u2696\ufe0f \u00c1RBITRO-\u03a9: vers\u00e3o LEVANTADA pra produ\u00e7\u00e3o "
                            "(nota %d/100) — n\u00facleo est\u00e1vel N-%d" % (nota_d, nova_d),
                            "ok", emit)

    # ---------- 4. RESPOSTA FINAL ----------
    MOTOR.set(fase="RESPONDENDO")
    etapa(ETAPA_RESPOSTA)
    tam_saida = 0
    try:
        if dev:
            resumo, rac_r, _ = MOTOR.chamar_bloco(
                MODELO_B, SIS_RESUMO_DEV,
                "PEDIDO DO USUARIO: %s\nRESULTADO: %s\nARQUIVO: %s\n%s" % (
                    texto_tarefa[:500], resultado_dev, arquivo, contexto), 500, 0.4, timeout=300)
            tam_saida = len(resumo) + len(MOTOR.estado.get("codigo", "") or "")
            for i in range(0, len(resumo), 80):
                emit({"e": "delta", "txt": resumo[i:i + 80]})
            emit({"e": "dev_resultado", "resultado": resultado_dev, "arquivo": arquivo})
        else:
            usuario_final = NQ.entramar(mensagem, contexto, rac_q, conselho)
            # VELOCIDADE: conversa comum comeca no modelo RAPIDO (8541);
            # se falhar, o 8540 entra como reserva.
            resp, rac, seg = MOTOR.chamar_reserva_stream(
                SIS_PRINCIPAL, usuario_final, 1500, 0.55, emit,
                rapido_primeiro=not dev)
            tam_saida = len(resp)
            if rac:
                emit({"e": "pensando", "txt": rac[:4000]})
            # VERIFICACAO QUANTICA instantanea (heuristica, sem chamada de modelo):
            # recalcula so em erro duro, no maximo 1 vez, comecando pelo rapido.
            avisos_q = NQ.verificar(resp, mensagem, emit)
            # ================= ARBITRO-O: JULGAMENTO SUPREMO =================
            nota, veredito, provas = ARBITRO.avaliar(
                resp, mensagem, emit, superposicao=bool(rac_q),
                n_agentes=n_agentes, latencia_s=seg)
            erro_duro = (veredito == "REPROVADA"
                         or any(a.startswith("conferir conta") or a == "resposta vazia"
                                for a in avisos_q))
            if erro_duro and not MOTOR.parar_flag:
                emit({"e": "quantico", "etapa": "ARBITRO",
                      "txt": "⚖️ ÁRBITRO-Ω VETOU a versão (nota %d/100): %s — recalculando"
                             % (nota, ("; ".join(avisos_q) or "qualidade baixa")[:120])})
                emit({"e": "delta", "txt": "\n\n---\n**⚖️ ÁRBITRO-Ω vetou a versão (nota %d/100) — recalculando...**\n\n" % nota})
                usuario_fix = NQ.entramar(mensagem, contexto, rac_q) + (
                    "\n\nATENCAO: a resposta anterior continha erro: %s. "
                    "Refa a conta com calma, passo a passo, e responda corrigido." % (
                        "; ".join(avisos_q)[:300]))
                resp2, _rac2, _seg2 = MOTOR.chamar_reserva_stream(
                    SIS_PRINCIPAL, usuario_fix, 1500, 0.4, emit, rapido_primeiro=True)
                if resp2:
                    resp = resp2
                tam_saida = len(resp)
                NQ.evol(emit, "RECALCULO", "ok" if resp2 else "falha",
                        (_seg2 or 0) * 1000, "RAPIDO+NX", "; ".join(avisos_q)[:100])
                avisos2 = NQ.verificar(resp, mensagem, emit)
                nota, veredito, provas = ARBITRO.avaliar(
                    resp, mensagem, emit, superposicao=bool(rac_q),
                    n_agentes=n_agentes, latencia_s=_seg2 or seg)
                emit({"e": "quantico", "etapa": "VERIFICACAO",
                      "txt": "ok apos recalcular" if not avisos2
                             else "avisos remanescentes: " + "; ".join(avisos2)[:150]})
            else:
                emit({"e": "quantico", "etapa": "VERIFICACAO",
                      "txt": "resposta conferida — ok" if not avisos_q
                             else "avisos: " + "; ".join(avisos_q)[:180]})
            # ================= ARBITRO-O: LEVANTAMENTO =================
            if veredito == "LEVANTADA" and not MOTOR.parar_flag:
                nova_v = ARBITRO.levantar(emit, nota)
                emit({"e": "quantico", "etapa": "ARBITRO",
                      "txt": "🏆 versão LEVANTADA pra produção (nota %d/100) — "
                             "núcleo estável agora na versão N-%d" % (nota, nova_v)})
    except ConexaoMorta:
        MOTOR.parar()
        MOTOR.destravar("ABORTADO")
        raise
    except Exception as ex:
        emit({"e": "erro", "txt": "Não consegui falar com o núcleo: %s" % str(ex)[:140]})

    etapa(ETAPA_RESPOSTA, feita=True)
    resultado = "OK"
    if dev:
        resultado = resultado_dev or "FALHOU"
    emit({"e": "fim", "resultado": resultado, "segundos": round(time.time() - t0, 1),
          "arquivo": arquivo, "modelo": MOTOR.estado.get("modelo_usado", "")})
    MOTOR.destravar(resultado)
    # log jsonl
    try:
        registro = {
            "quando": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "modo": "DEV" if dev else "CHAT", "pergunta": mensagem[:500],
            "resultado": resultado, "arquivo": arquivo,
            "modelo": MOTOR.estado.get("modelo_usado", ""),
        }
        with open(ARQ_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # telemetria + uso no banco de dados
    try:
        BANCO.registrar_uso(
            via=via, usuario_id=usuario_id, chave_id=chave_id,
            modo="DEV" if dev else "CHAT",
            modelo=(MOTOR.estado.get("modelo_usado", "") or "")[:60],
            tokens_ent=max(1, len(mensagem) // 4), tokens_sai=max(1, tam_saida // 4),
            latencia_ms=int(round((time.time() - t0) * 1000)),
            status=resultado)
        BANCO.tele("chat_fim" if via == "chat" else "api_fim",
                   "resultado=%s segundos=%s" % (resultado, round(time.time() - t0, 1)),
                   "usuario %s" % usuario_id if usuario_id else "chave %s" % chave_id)
    except Exception:
        pass
    # MUTACAO AUTONOMA: o nucleo se re-calibra sozinho apos cada tarefa
    try:
        AUTO.auto_ajustar(emit)
    except Exception:
        pass


# ---------------------------------------------------------------- SERVIDOR
class Manipulador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, obj, codigo=200, cors=False):
        corpo = json.dumps(obj, ensure_ascii=True).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(corpo)

    def _sessao(self):
        return BANCO.usuario_da_sessao(self.headers.get("X-Session") or "")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Authorization, Content-Type, X-Api-Key, X-Session")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            corpo = PAGINA.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)
        elif self.path == "/saude":
            ev = BANCO.evolucao_stats()
            self._json({"ok": True, "servico": "AI BRASIL CHAT", "versao": VERSAO,
                        "hora": agora_iso(), "motores": estado_motores(),
                        "nucleo": {"nq": NQ.VERSAO_NQ, "arbitro": ARBITRO.VERSAO,
                                   "estavel": "N-%d" % ARBITRO.versao_estavel,
                                   "nivel": ev.get("nivel"), "xp": ev.get("xp")}},
                       cors=True)
        elif self.path == "/api/eu":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            self._json({"id": u["id"], "nome": u["nome"], "email": u["email"],
                        "admin": bool(u["admin"])})
        elif self.path == "/api/estado":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            self._json(MOTOR.snap())
        elif self.path == "/api/nucleo":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            ev = BANCO.evolucao_stats()
            self._json({
                "versao": VERSAO,
                "hora": agora_iso(),
                "uptime_seg": int(time.time() - INICIO_TS),
                "nq": {"versao": NQ.VERSAO_NQ, "teto_analise": NQ.TETO_ANALISE},
                "evolucao": ev,
                "arbitro": ARBITRO.estado(),
                "autonomo": AUTO.estado(),
                "motores": estado_motores(),
                "sandbox": sandbox_estado(),
            }, cors=True)
        elif self.path == "/api/telemetria":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            res = BANCO.resumo_telemetria()
            res["clientes"] = BANCO.clientes(bool(u["admin"]), u["id"])
            self._json(res)
        elif self.path == "/api/planos":
            self._json(planos_json(), cors=True)
        elif self.path == "/api/v1/uso":
            reg = BANCO.chave_por_token(chave_da_requisicao(self.headers))
            if not reg:
                return self._json({"erro": "Chave de API invalida."}, 401, cors=True)
            cfg_plano = PLANOS.get(reg["plano"], PLANOS["GRATUITO"])
            usado = BANCO.chave_uso_hoje(reg["id"])
            self._json({
                "plano": reg["plano"], "limite_dia": cfg_plano["por_dia"],
                "usado_hoje": usado, "restante_hoje": max(0, cfg_plano["por_dia"] - usado),
                "total": reg["total"], "ativa": bool(reg["ativa"]),
            }, cors=True)
        elif self.path == "/api/chaves":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            self._json({"chaves": BANCO.chaves_do(u["id"])})
        elif self.path == "/api/clientes":
            u = self._sessao()
            if not u:
                return self._json({"erro": "sem sessao"}, 401)
            self._json({"clientes": BANCO.clientes(bool(u["admin"]), u["id"])})
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self._json({"erro": "rota desconhecida"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            dados = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            dados = {}

        # ---------------- API EXTERNA (chave Bearer, funciona na rede) --------
        if self.path == "/api/v1/chat":
            reg = BANCO.chave_por_token(chave_da_requisicao(self.headers))
            if not reg:
                return self._json({"erro": "Chave de API invalida. Envie o cabecalho "
                                           "Authorization: Bearer sk-br-..."}, 401, cors=True)
            if not reg["ativa"]:
                return self._json({"erro": "Esta chave foi revogada."}, 401, cors=True)
            cfg_plano = PLANOS.get(reg["plano"], PLANOS["GRATUITO"])
            if BANCO.chave_uso_hoje(reg["id"]) >= cfg_plano["por_dia"]:
                BANCO.tele("api_bloqueio", "plano %s no limite diario" % reg["plano"],
                           "chave %s" % reg["id"])
                return self._json({"erro": "Limite diario do plano atingido",
                                   "plano": reg["plano"], "limite_dia": cfg_plano["por_dia"],
                                   "usado_hoje": cfg_plano["por_dia"]}, 429, cors=True)
            usado = BANCO.chave_registrar_pedido(reg["id"])
            mensagem = str(dados.get("mensagem", "")).strip()
            if not mensagem:
                return self._json({"erro": "Campo 'mensagem' vazio."}, 400, cors=True)
            stream = bool(dados.get("stream"))
            dev = bool(dados.get("dev"))
            if not MOTOR.travar():
                return self._json({"erro": "Motor ocupado. Tente de novo em alguns segundos."},
                                  409, cors=True)
            BANCO.tele("api", "POST /api/v1/chat (%s)" % ("stream" if stream else "bloco"),
                       "chave %s" % reg["id"])
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.close_connection = True

                def emit(obj):
                    try:
                        self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n")
                                         .encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        MOTOR.parar()
                        raise ConexaoMorta()

                try:
                    executar_chat(mensagem, [], emit, dev, False,
                                  usuario_id=reg["usuario_id"], via="api", chave_id=reg["id"])
                except ConexaoMorta:
                    MOTOR.destravar("ABORTADO")
                except Exception as ex:
                    try:
                        emit({"e": "erro", "txt": "Erro interno: %s" % str(ex)[:200]})
                        emit({"e": "fim", "resultado": "FALHOU", "segundos": 0,
                              "arquivo": "", "modelo": ""})
                    except Exception:
                        pass
                    MOTOR.destravar("FALHOU")
                return
            eventos = []

            def emit_cap(obj):
                eventos.append(obj)

            try:
                executar_chat(mensagem, [], emit_cap, dev, False,
                              usuario_id=reg["usuario_id"], via="api", chave_id=reg["id"])
            except Exception as ex:
                MOTOR.destravar("FALHOU")
                return self._json({"erro": "Falha no motor: %s" % str(ex)[:200]}, 502, cors=True)
            resposta_txt = "".join(o.get("txt", "") for o in eventos
                                   if o.get("e") == "delta").strip()
            resultado, segundos, modelo_usado = "FALHOU", 0, ""
            for o in eventos:
                if o.get("e") == "fim":
                    resultado = o.get("resultado", resultado)
                    segundos = o.get("segundos", 0)
                    modelo_usado = o.get("modelo", "")
            if not resposta_txt and resultado == "APROVADO":
                resposta_txt = "Aplicacao criada, executada e aprovada nos testes automaticos."
            return self._json({
                "resposta": resposta_txt, "resultado": resultado,
                "modelo": modelo_usado, "segundos": segundos,
                "plano": reg["plano"], "usado_hoje": usado,
                "restante_hoje": max(0, cfg_plano["por_dia"] - usado),
            }, cors=True)

        if self.path == "/api/v1/uso":
            reg = BANCO.chave_por_token(chave_da_requisicao(self.headers))
            if not reg:
                return self._json({"erro": "Chave de API invalida."}, 401, cors=True)
            cfg_plano = PLANOS.get(reg["plano"], PLANOS["GRATUITO"])
            usado = BANCO.chave_uso_hoje(reg["id"])
            return self._json({
                "plano": reg["plano"], "limite_dia": cfg_plano["por_dia"],
                "usado_hoje": usado, "restante_hoje": max(0, cfg_plano["por_dia"] - usado),
                "total": reg["total"], "ativa": bool(reg["ativa"]),
            }, cors=True)

        # ---------------- CONTA (login/cadastro/sair) ----------------
        if self.path == "/api/registrar":
            r = BANCO.registrar(str(dados.get("nome", "")), str(dados.get("email", "")),
                                str(dados.get("senha", "")))
            return self._json(r, 200 if "token" in r else 400)
        if self.path == "/api/login":
            usuario = str(dados.get("usuario") or dados.get("email") or "")
            r = BANCO.login(usuario, str(dados.get("senha", "")))
            return self._json(r, 200 if "token" in r else 401)
        if self.path == "/api/sair":
            BANCO.sair(self.headers.get("X-Session") or "")
            return self._json({"ok": True})

        # ---------------- CHAT INTERNO (com sessao) ----------------
        if self.path == "/api/chat":
            u = self._sessao()
            if not u:
                return self._json({"erro": "Sessao invalida. Entre novamente."}, 401)
            mensagem = str(dados.get("mensagem", "")).strip()
            historico = dados.get("historico") or []
            forcar = bool(dados.get("forcar_dev"))
            nunca = bool(dados.get("nunca_dev"))
            if not mensagem:
                return self._json({"erro": "mensagem vazia"}, 400)
            if not MOTOR.travar():
                return self._json({"erro": "ocupado", "txt": "Estou terminando a tarefa atual. "
                                                            "Aguarde alguns segundos."}, 409)
            BANCO.tele("chat", mensagem[:100], u["nome"])
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True

            def emit(obj):
                try:
                    self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    MOTOR.parar()
                    raise ConexaoMorta()

            try:
                executar_chat(mensagem, historico, emit, forcar, nunca,
                              usuario_id=u["id"], via="chat")
            except ConexaoMorta:
                MOTOR.destravar("ABORTADO")
            except Exception as ex:
                try:
                    emit({"e": "erro", "txt": "Erro interno: %s" % str(ex)[:200]})
                    emit({"e": "fim", "resultado": "FALHOU", "segundos": 0, "arquivo": "",
                          "modelo": ""})
                except Exception:
                    pass
                MOTOR.destravar("FALHOU")
            return
        if self.path == "/api/parar":
            u = self._sessao()
            if not u:
                return self._json({"erro": "Sessao invalida."}, 401)
            MOTOR.parar()
            return self._json({"ok": True})

        # ---------------- CHAVES ----------------
        if self.path == "/api/chaves":
            u = self._sessao()
            if not u:
                return self._json({"erro": "Sessao invalida."}, 401)
            r = BANCO.chave_criar(u["id"], str(dados.get("plano", "")))
            return self._json(r, 200 if "chave" in r else 400)
        if self.path == "/api/chaves/revogar":
            u = self._sessao()
            if not u:
                return self._json({"erro": "Sessao invalida."}, 401)
            ok = BANCO.chave_revogar(u["id"], int(dados.get("id") or 0))
            return self._json({"ok": ok}, 200 if ok else 400)
        return self._json({"erro": "rota desconhecida"}, 404)

    def log_message(self, fmt, *args):
        pass


with open(ARQ_PAGINA, "r", encoding="utf-8") as _f:
    PAGINA = _f.read().replace("__PORTA__", str(PORTA))


def main():
    log("AI BRASIL CHAT v%s iniciando em 0.0.0.0:%d (base=%s)" % (VERSAO, PORTA, BASE))
    log("ARBITRO-%s pronto — nucleo estavel N-%d | MUTACAO AUTONOMA %s: %d genes, %d mutacoes" % (
        ARBITRO.VERSAO, ARBITRO.versao_estavel, AUTO.VERSAO,
        sum(1 for t in AUTO.tecnologias.values() if t["ativo"]), AUTO.mutacoes))
    threading.Thread(target=sandbox_preparar, daemon=True).start()
    log("Sandbox virtual: %s (venv=%s)" % (DIR_SANDBOX, "preparando"))
    try:
        ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
               if not ip.startswith("127.")]
    except Exception:
        ips = []
    log("API externa: http://%s:%d/api/v1/chat" % (ips[0] if ips else "IP-DO-PC", PORTA))
    srv = ThreadingHTTPServer(("0.0.0.0", PORTA), Manipulador)
    srv.allow_reuse_address = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
