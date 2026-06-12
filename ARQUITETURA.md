# 🏗️ Arquitetura & Roteiro de Defesa — Bolão da Copa do Mundo

> Documento de apoio para a apresentação da A3 (UC **Sistemas Distribuídos e
> Mobile** / **Usabilidade, Desenvolvimento Web, Mobile e Jogos**).
> **Todos do grupo devem entender este documento** — a nota é coletiva.

## 1. Visão geral

O projeto é um **sistema distribuído** de bolão da Copa do Mundo 2026: um
**cliente web** que se comunica, **por rede**, com um **servidor/microsserviço
na nuvem**, que por sua vez persiste em um **banco de dados na nuvem**. O
servidor expõe, além da interface web, uma **API REST (JSON)** — um
microsserviço que pode ser consumido por outros clientes/integrações.

```
                    ┌─────────────────────────┐
                    │      CLIENTE WEB         │
                    │  Navegador (PC/celular)  │
                    │  HTML + Tailwind + JS     │
                    └────────────┬────────────┘
                                 │  HTTP
                   ┌─────────────┴─────────────┐
                   │  páginas (cookie JWT)      │  API REST (Bearer JWT)
                   ▼                             ▼
        ┌───────────────────────────────────────────────┐
        │   SERVIDOR / MICROSSERVIÇO (nuvem)             │
        │   FastAPI  ·  Vercel (serverless, stateless)   │
        │   - Interface web (Jinja2)                     │
        │   - API REST  /api/*  (JSON)                   │
        │   - Autenticação JWT  - Regras / pontuação     │
        └───────────────────────┬───────────────────────┘
                                 │  TCP (protocolo Postgres) via pooler
                                 ▼
        ┌───────────────────────────────────────────────┐
        │   BANCO DE DADOS NA NUVEM                      │
        │   Supabase PostgreSQL  (pooler / pgBouncer)    │
        └───────────────────────────────────────────────┘
```

**Repositório:** GitHub (privado) com **deploy contínuo** — todo push publica
na Vercel automaticamente.

## 2. Componentes e responsabilidades

| Componente | Tecnologia | Papel no sistema distribuído |
|---|---|---|
| Cliente Web | HTML, Tailwind, JS, Jinja2 | Interface de acesso (navegador, responsiva) |
| Servidor/API | FastAPI (Python) | Microsserviço: web + **API RESTful** + regras |
| Hospedagem | Vercel (serverless) | Computação **stateless** escalável na nuvem |
| Banco | Supabase PostgreSQL | **Banco de dados na nuvem** (estado compartilhado) |
| Pooler | pgBouncer (Supabase) | Multiplexação de conexões entre serviços |
| Auth | JWT (cookie na web, Bearer na API) | Sessão **sem estado** no servidor |

## 3. Como o projeto atende ao edital (Opção 2)

A opção 2 considera integrado à disciplina de Sistemas Distribuídos *"o
acoplamento de alguma tecnologia da nuvem como microsserviço API RESTful bem
como utilização de banco de dados na nuvem"*.

| Requisito do edital | Onde está atendido |
|---|---|
| Sistema web responsivo (PC → mobile) | Templates Jinja2 + Tailwind, layout responsivo |
| **CRUD em banco de dados** | Usuários, jogos e palpites (criar/ler/editar/excluir) |
| **Banco de dados na nuvem** | Supabase PostgreSQL |
| **Microsserviço / API RESTful** | Endpoints `/api/*` em JSON (FastAPI) |
| Tecnologia de nuvem acoplada | Deploy serverless (Vercel) + DB gerenciado (Supabase) |

> Observação sobre Bootstrap: o edital cita Bootstrap; usamos **Tailwind CSS**,
> que cumpre o mesmo papel (framework CSS utilitário com responsividade).
> Confirme com o professor se aceita; se exigir Bootstrap, é uma troca de classes.

## 4. Endpoints da API REST (microsserviço)

Base: `https://bolao-copa-topaz.vercel.app/api`

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| POST | `/auth/register` | Cria conta e retorna token | — |
| POST | `/auth/login` | Autentica e retorna token | — |
| GET | `/me` | Dados + pontuação do usuário | Bearer |
| GET | `/jogos` | Lista jogos + palpite do usuário | Bearer |
| POST | `/palpites/{id}` | Cria/edita palpite (CRUD) | Bearer |
| GET | `/ranking` | Ranking geral | Bearer |
| GET | `/historico` | Jogos finalizados + pontos | Bearer |

Erros seguem HTTP: `401` (sem/expirado token), `403` (admin não palpita),
`404` (jogo inexistente), `409` (palpite travado), `422` (dados inválidos).

**Demonstrar a API:** em um navegador/Postman/`curl`, faça `POST /api/auth/login`
(recebe um token) e depois `GET /api/jogos` com o header
`Authorization: Bearer <token>` — a resposta é **JSON**, provando o microsserviço.

## 5. Conceitos de Sistemas Distribuídos demonstrados

- **Cliente-servidor multicamadas:** cliente (navegador), servidor (FastAPI) e
  banco (Supabase) em **serviços/máquinas diferentes**, comunicando por rede.
- **Comunicação por mensagens (HTTP/REST):** a API expõe um contrato JSON com
  métodos e códigos de status padronizados — independente de linguagem/cliente.
- **Computação stateless + estado externalizado:** o servidor roda como funções
  serverless (várias instâncias podem atender em paralelo); todo o estado fica no
  banco compartilhado. Padrão clássico de escalabilidade horizontal.
- **Autenticação sem sessão de servidor (JWT):** o token carrega a identidade;
  qualquer instância atende qualquer requisição (sem afinidade de sessão).
- **Pooling de conexões (pgBouncer):** intermediário que multiplexa conexões
  entre o servidor e o banco — infraestrutura distribuída real.
- **Consistência e concorrência:** transações + restrição única
  `(usuario_id, jogo_id)` garantem 1 palpite por jogo mesmo com acessos
  simultâneos; a pontuação é gravada na transação do resultado.
- **Sincronização de estado entre clientes (tabela "Ao Vivo"):** quando o admin
  registra um gol, o placar parcial vira estado compartilhado no servidor/banco;
  os vários clientes (em máquinas diferentes) fazem **polling** (auto-refresh) e
  **convergem** para o mesmo placar/pontuação provisória logo depois — uma
  ilustração de **consistência eventual** e sincronização cliente-servidor.

## 6. Roteiro de defesa (perguntas prováveis)

- **"Por que isso é um sistema distribuído?"** → Há componentes autônomos
  (cliente web, servidor, banco) em **processos/máquinas separados**, cooperando
  por **rede** com protocolos definidos (HTTP/REST e protocolo Postgres).
- **"Onde está o microsserviço/API?"** → Em `app/routes/api.py`: endpoints REST
  em JSON (mostrar uma resposta com `curl`/navegador).
- **"Onde está o banco na nuvem?"** → Supabase (PostgreSQL gerenciado), acessado
  por connection string via pooler (porta 6543).
- **"Como funciona a autenticação?"** → JWT: o servidor assina um token no login;
  o cliente o envia a cada requisição (cookie na web; header
  `Authorization: Bearer` na API); o servidor valida a assinatura.
- **"E se dois usuários palpitarem ao mesmo tempo?"** → Cada um tem sua sessão e
  sua linha; a restrição única + transações garantem consistência.
- **"Como vocês fazem o deploy?"** → Git + Vercel: push na `main` → build e
  publicação automáticos (CI/CD).

## 7. Como rodar / demonstrar

**Aplicação (já no ar):** https://bolao-copa-topaz.vercel.app
- Admin (registra resultados): `admin@bolao.com` / senha definida no `.env`.

**Roteiro sugerido (5–8 min):**
1. Abrir o **site** → cadastrar/entrar como participante; mostrar jogos e ranking.
2. Registrar um **palpite** (CRUD no **banco na nuvem**).
3. Mostrar a **API REST** respondendo em JSON (`/api/jogos` com token) — o
   microsserviço.
4. Entrar como **admin** e registrar um **resultado** → mostrar a **pontuação e o
   ranking** mudando para todos (estado compartilhado na nuvem).
5. Fechar com o **diagrama** desta página explicando as camadas e a comunicação.

## 8. Para a equipe (todos devem saber tudo)

Mesmo com tarefas divididas, **cada integrante deve saber explicar**: (a) o que é
o sistema distribuído, (b) onde está a API/microsserviço, (c) onde está o banco
na nuvem, (d) como funciona a autenticação, (e) como é feito o deploy. O edital
avisa: *"não existe 'minha parte foi essa'"*.
