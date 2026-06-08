# 🏗️ Arquitetura & Roteiro de Defesa — Bolão da Copa do Mundo Arianjo

> Documento de apoio para a apresentação da A3 (UC **Sistemas Distribuídos e
> Mobile** / **Usabilidade, Desenvolvimento Web, Mobile e Jogos**).
> **Todos do grupo devem entender este documento** — a nota é coletiva.

## 1. Visão geral

O projeto é um **sistema distribuído** de bolão da Copa do Mundo 2026, composto
por **clientes independentes** (web e mobile) que se comunicam por **rede** com
um **microsserviço na nuvem**, que por sua vez persiste em um **banco de dados
na nuvem**.

```
        ┌─────────────────────┐         ┌─────────────────────┐
        │   CLIENTE WEB        │         │   CLIENTE MOBILE     │
        │  (navegador)         │         │  React Native /Expo  │
        │  HTML+Tailwind+JS    │         │  + SENSOR (acelerôm.)│
        └──────────┬──────────┘         └──────────┬──────────┘
                   │  HTTP (HTML)                   │  HTTP/JSON (REST)
                   │  cookie JWT                    │  Bearer JWT
                   └───────────────┬───────────────┘
                                   ▼
                   ┌───────────────────────────────────┐
                   │   SERVIDOR / MICROSSERVIÇO (nuvem) │
                   │   FastAPI  ·  Vercel (serverless)  │
                   │   - Web (Jinja2)  - API REST /api  │
                   │   - Auth JWT      - Regras/pontuação│
                   └───────────────┬───────────────────┘
                                   │  TCP (protocolo Postgres) via pooler
                                   ▼
                   ┌───────────────────────────────────┐
                   │   BANCO DE DADOS NA NUVEM          │
                   │   Supabase PostgreSQL (pgBouncer)  │
                   └───────────────────────────────────┘
```

**Repositório:** GitHub (privado) com **deploy contínuo** — todo push publica
na Vercel automaticamente.

## 2. Componentes e responsabilidades

| Componente | Tecnologia | Papel no sistema distribuído |
|---|---|---|
| Cliente Web | HTML, Tailwind, JS, Jinja2 | Interface de acesso (navegador) |
| Cliente Mobile | React Native (Expo) | Interface de acesso móvel + **sensor** |
| Servidor/API | FastAPI (Python) | Microsserviço: regras de negócio + **API RESTful** |
| Hospedagem | Vercel (serverless) | Computação **stateless** escalável na nuvem |
| Banco | Supabase PostgreSQL | **Banco de dados na nuvem** (estado compartilhado) |
| Pooler | pgBouncer (Supabase) | Multiplexação de conexões entre serviços |
| Auth | JWT (cookie na web, Bearer no mobile) | Sessão **sem estado** no servidor |

## 3. Como o projeto atende ao edital (Opção 2)

| Requisito do edital | Onde está atendido |
|---|---|
| Sistema web responsivo (PC → mobile) | Templates Jinja2 + Tailwind, layout responsivo |
| **CRUD em banco de dados** | Usuários, jogos e palpites (criar/ler/editar/excluir) |
| **App mobile (React Native) com CRUD** | `mobile/` — login, jogos, **palpites (CRUD)**, ranking |
| **Banco de dados na nuvem** | Supabase PostgreSQL |
| **Microsserviço / API RESTful** | Endpoints `/api/*` em JSON (FastAPI) |
| **Coleta de dados via sensor** | Acelerômetro do celular (`useShake.js`) — chacoalhar p/ atualizar |
| Tecnologia de nuvem acoplada | Deploy serverless (Vercel) + DB gerenciado (Supabase) |

> Observação sobre Bootstrap: o edital cita Bootstrap; usamos **Tailwind CSS**,
> que cumpre o mesmo papel (framework CSS utilitário com responsividade). Se o
> professor exigir Bootstrap especificamente, é uma troca pontual de classes.

## 4. Endpoints da API REST

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

## 5. Conceitos de Sistemas Distribuídos demonstrados

- **Cliente-servidor multicamadas:** dois clientes distintos (web e mobile) e um
  servidor, em máquinas/serviços diferentes, comunicando por rede.
- **Comunicação por mensagens (HTTP/REST):** API RESTful com JSON, métodos e
  códigos de status padronizados — contrato independente de linguagem.
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
- **Coleta de dados por sensor:** o acelerômetro do dispositivo gera eventos que
  acionam sincronização com o servidor.

## 6. Roteiro de defesa (perguntas prováveis)

- **"Por que isso é um sistema distribuído?"** → Há componentes autônomos
  (clientes web/mobile, servidor, banco) em **processos/máquinas separados**,
  cooperando por **rede** com protocolos definidos (HTTP/REST e Postgres).
- **"Onde está o microsserviço/API?"** → Em `app/routes/api.py`: endpoints REST
  em JSON, consumidos pelo app mobile (mostrar uma requisição no celular).
- **"Onde está o banco na nuvem?"** → Supabase (PostgreSQL gerenciado), acessado
  por connection string via pooler (porta 6543).
- **"Onde está o sensor?"** → `mobile/src/hooks/useShake.js` (acelerômetro).
  Demonstrar **chacoalhando o celular** para atualizar a lista.
- **"Como funciona a autenticação entre os serviços?"** → JWT: o servidor assina
  um token no login; o cliente o envia a cada requisição (cookie na web, header
  `Authorization: Bearer` no mobile); o servidor valida a assinatura.
- **"E se dois usuários palpitarem ao mesmo tempo?"** → Cada um tem sua sessão e
  sua linha; a restrição única + transações garantem consistência.
- **"Como vocês fazem o deploy?"** → Git + Vercel: push na `main` → build e
  publicação automáticos (CI/CD).

## 7. Como rodar tudo (para a apresentação)

**Backend/web (já no ar):** https://bolao-copa-topaz.vercel.app
- Admin (registra resultados): `admin@bolao.com` / senha definida no `.env`.

**App mobile:**
```bash
cd mobile
npm install
npx expo start    # abrir no Expo Go e escanear o QR code
```

**Roteiro sugerido de demonstração (5–8 min):**
1. Abrir o **site** → mostrar jogos/ranking (cliente web).
2. Abrir o **app no celular** → cadastrar/entrar (mostra a **API REST** em ação).
3. Registrar um **palpite** no celular (CRUD no **banco na nuvem**).
4. **Chacoalhar o celular** → dados atualizam (**sensor**).
5. No site, logar como **admin** e registrar um **resultado** → mostrar a
   **pontuação e o ranking** mudando para todos (estado compartilhado).
6. Fechar com o **diagrama** desta página explicando as camadas.

## 8. Divisão sugerida de domínio (todos devem saber tudo)

Mesmo com tarefas divididas, **cada integrante deve saber explicar**: (a) o que é
o sistema distribuído, (b) onde está a API/microsserviço, (c) onde está o banco
na nuvem, (d) onde está o sensor, (e) como funciona a autenticação. O edital
avisa: *"não existe 'minha parte foi essa'"*.
