# STARLA ⚛️ — Primeira LLM Quântica do Brasil
### (AI BRASIL CHAT v9.8 — núcleo de raciocínio quântico 100% offline)

**STARLA** é um sistema de IA completo que roda **100% offline no seu PC**, com um
núcleo de raciocínio quântico proprietário, um **ÁRBITRO-Ω** que julga cada versão
do código (nota 0–100), uma **MUTAÇÃO AUTÔNOMA** que recalibra o sistema sozinha
e um painel ao vivo dentro do chat.

> Sem nuvem. Sem enviar dados pra fora. Contas, chaves, telemetria — tudo em
> SQLite local, na sua máquina.

---

## ⚛️ O que é o núcleo quântico

O coração do STARLA é o **NÚCLEO QUÂNTICO TURBO** (`quantico` v3.5-evolucao):

- **Superposição** — dispara paralela no modelo rápido com teto duro de 90s
  (se falhar, o chat segue direto — nunca trava)
- **Verificação instantânea** por heurística (conta sem número, resposta vazia, loop)
- **Recálculo** no máximo 1 vez em erro duro
- **XP e níveis** — o núcleo evolui: cada operação dá XP, sobe de nível
  (Nível 1 = "Semente Quântica"), eventos gravados em NDJSON

## ⚖️ ÁRBITRO-Ω (Ω-1.0)

Avaliador supremo do sistema:

- Julga **cada versão** gerada pelo modo DEV
- Dá **nota 0–100** (nota mínima para aprovação: **75**)
- **Aprova ou reprova** — reprovadas ficam registradas (`reprovadas`)
- **Levanta a melhor versão pra produção** (`versao_estavel` N-0, N-1, N-2...)

## 🧬 MUTAÇÃO AUTÔNOMA (AUTO-1.0)

O sistema se recalibra sozinho após cada tarefa:

- **Genoma de tecnologias** — detecta os "poderes" disponíveis no PC:
  numpy 🧮, matplotlib 📊, requests 🌐, PIL 🖼️, ctypes 🔧, winreg 💾,
  pandas, onnxruntime...
- **Tetos dinâmicos** — `teto_agentes`, `prazo_agentes`, `teto_analise`
  recalibrados conforme o desempenho real
- **Mutações registradas** — todo ajuste feito por ele mesmo fica no histórico

## 💻 Modo DEV (agente programador)

- Gera código, executa **de verdade** em sandbox com `venv` isolado
- Lê o erro real, corrige sozinho (até 4 tentativas) e resume o resultado
- Cada versão final passa pelo **ÁRBITRO-Ω** antes de virar estável

## 📡 Painel ao vivo (dentro do chat)

Painel lateral (390px) alimentado por `/api/nucleo` em tempo real:

- XP, nível, execuções por operador (SUPERPOSIÇÃO, ENTRELACE, AGENTE, AUTÔNOMO)
- Leitura de eventos NDJSON ao vivo (genoma, falhas, aplicados)
- Estado do ÁRBITRO-Ω (versão estável, reprovadas, nota mínima)
- Genoma da MUTAÇÃO AUTÔNOMA (genes ativos/inativos) e tetos atuais
- Motores 8540/8541 e últimas execuções do sandbox

## 🌐 API externa

Chaves `sk-br-...` com planos (Gratuito 50/dia · Prata 300/dia · Ouro 2000/dia),
limites e telemetria por chave:

```
POST /api/v1/chat
Authorization: Bearer sk-br-SUA-CHAVE
{"mensagem": "ola"}
```

## 🚀 Como rodar

1. Instale **Python 3.12+**
2. Suba 2 modelos no **LM Studio** (ou `llama-server`):
   - porta **8540** = modelo pesado (NX-8B, raciocina com `<think>`)
   - porta **8541** = modelo rápido (RAPIDO, também raciocina)
3. `python AI-BRASIL-CHAT.py`
4. Abra **http://127.0.0.1:8580**
5. Crie sua conta admin: edite no topo do `AI-BRASIL-CHAT.py`
   `NOME_ADMIN`, `EMAIL_ADMIN` e `SENHA_ADMIN` (vêm com placeholders)

**Windows em background:** `LIGA-CHAT.ps1` (liga oculto e mostra o /saude) e
`PARA-CHAT.ps1` (para e confirma a porta livre). Também tem `.bat` equivalentes.

## 🔌 Portas

| Porta | Uso |
|---|---|
| 8580 | STARLA / AI BRASIL CHAT (interface + API) |
| 8540 | Modelo pesado (raciocínio) |
| 8541 | Modelo rápido (resposta) |

## 🔒 Segurança

- ⚠️ **Nunca** publique sua senha admin nem chaves `sk-br-` de verdade
  (o código deste repositório vem só com placeholders)
- Senhas de login viram hash SHA-256 com sal aleatório no banco local
- Sessões por token (`X-Session`); API externa por `Bearer sk-br-...`
- Básico roda em `127.0.0.1`; pra rede local, libere a 8580 no firewall
- `.gitignore` já exclui banco, logs, backups e pastas de teste

## 🗂️ Estrutura

```
AI-BRASIL-CHAT/
├── AI-BRASIL-CHAT.py    # servidor + núcleo quântico + ÁRBITRO-Ω + MUTAÇÃO
├── AI-BRASIL-CHAT.html  # interface + painel ao vivo (single file)
├── LIGA-CHAT.bat/.ps1   # liga em background (Windows)
├── PARA-CHAT.bat/.ps1   # para e confirma porta livre
└── .gitignore
```

---

## ©️ Direitos autorais

**Copyright © 2026 Samuel Fernandes (Chefe) — IA Brasil / Projeto STARLA.**
Todos os direitos reservados.

Este software é obra autoral do autor. É permitido usar, estudar e modificar
**para uso pessoal e educacional**. É **proibido** vender, sublicenciar ou
redistribuir comercialmente sem autorização por escrito do autor.
O nome **STARLA**, o **ÁRBITRO-Ω** e a **MUTAÇÃO AUTÔNOMA** fazem parte da
identidade do projeto.

Feito no Brasil 🇧🇷 — código e dados 100% seus.
