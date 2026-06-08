# 🏆 Bolão da Copa do Mundo Arianjo

Sistema completo de bolão da Copa do Mundo 2026 (formato 48 times / 12 grupos),
para ~8 participantes. Cada usuário cria conta, registra palpites, acompanha
jogos, ranking e histórico; o administrador cadastra jogos, registra resultados
(com pontuação automática) e controla o chaveamento do mata-mata.

> **Sistema distribuído:** clientes **web** e **mobile** (React Native) que
> conversam com um **microsserviço REST** (FastAPI na nuvem) e um **banco na
> nuvem** (Supabase). O app mobile usa o **sensor acelerômetro**. A arquitetura,
> os requisitos atendidos e o roteiro de defesa estão em
> [ARQUITETURA.md](ARQUITETURA.md). O app mobile está em [mobile/](mobile/).

## 🧱 Stack

| Camada        | Tecnologia                                   |
| ------------- | -------------------------------------------- |
| Backend       | Python · FastAPI                             |
| Web           | Jinja2 · Tailwind CSS · JavaScript           |
| Mobile        | React Native (Expo) + expo-sensors           |
| API           | REST/JSON (`/api/*`) com JWT Bearer          |
| ORM           | SQLAlchemy 2.x                               |
| Banco         | Supabase PostgreSQL (pooler em serverless)   |
| Autenticação  | JWT (cookie na web, Bearer no mobile) + bcrypt |
| Migrations    | Alembic                                      |
| Deploy        | Vercel (Python ASGI)                         |

> **Requer Python 3.10+** (a Vercel usa 3.12). A sintaxe moderna de tipos
> (`int | None`) é usada em todo o projeto.

## 📂 Estrutura

```
app/
  config.py            Configurações (pydantic-settings, lê .env)
  database/            Base, engine (NullPool) e sessão
  models/              usuarios · jogos · palpites (+ enums Fase/Status)
  schemas/             Validação Pydantic dos formulários
  auth/                Hash bcrypt, JWT, cookies e dependencies de rota
  services/            scoring · ranking · palpites (travamento)
  routes/              auth · dashboard · jogos · palpites · ranking · historico · admin
  templates/           Jinja2 (base, parciais e telas)
  static/              CSS (Tailwind) e JS
  main.py              Application factory (app)
migrations/            Alembic
scripts/seed.py        Seed da Copa 2026
api/index.py           Entrypoint da Vercel
```

## 🧮 Regras de pontuação

**Fase de grupos**
- Placar exato → **3 pontos**
- Acertou o resultado (vitória/empate) → **1 ponto**
- Errou → **0**

**Mata-mata** (o classificado faz parte do resultado; empate sozinho não pontua)
- Placar exato **+** classificado correto → **3 pontos**
- Classificado correto (placar errado) → **1 ponto**
- Acertou empate mas errou quem avança → **0**

A pontuação é **gravada** quando o admin registra o resultado oficial — nunca
recalculada a cada carregamento de página. Palpites **travam** automaticamente
no horário do jogo ou quando o admin fecha o jogo.

---

## 🚀 Rodando localmente

### 1. Ambiente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# edite o .env (veja as opções abaixo)
```

Gere uma `SECRET_KEY` forte:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Para desenvolvimento rápido **sem Supabase**, use SQLite no `.env`:

```env
DATABASE_URL=sqlite:///./bolao_dev.db
SECRET_KEY=<sua-chave>
ADMIN_EMAIL=seu-email@exemplo.com
ENVIRONMENT=development
```

### 3. Criar o schema + seed

```bash
alembic upgrade head        # cria as tabelas
python -m scripts.seed      # cria os 104 jogos da Copa 2026
# (use "python -m scripts.seed --reset" para recriar do zero)
```

### 4. Criar o administrador padrão (login fixo)

O admin é uma conta fixa criada direto no banco — não depende de cadastro.
Defina `ADMIN_EMAIL` e `ADMIN_PASSWORD` no `.env` e rode:

```bash
python -m scripts.create_admin
```

Faça login em `/login` com essas credenciais. O script é idempotente: rodá-lo
de novo **redefine a senha** do admin (útil para resetar).

> Também existe um atalho: quem se cadastrar em `/cadastro` com um email igual
> ao `ADMIN_EMAIL` vira admin automaticamente. O caminho recomendado, porém, é
> o `create_admin` acima.

### 5. Subir o servidor

```bash
uvicorn app.main:app --reload
```

Acesse <http://localhost:8000> e entre em `/login` como admin. Demais cadastros
em `/cadastro` são participantes comuns.

---

## 🗄️ Configurando o Supabase

1. Crie um projeto em <https://supabase.com> e defina uma senha de banco.
2. No painel: **Project Settings → Database → Connection string → "Transaction"**.
   Use o **pooler** (host `...pooler.supabase.com`, porta **6543**) — essencial
   para ambientes serverless.
3. Monte a `DATABASE_URL` com o driver psycopg2:

   ```env
   DATABASE_URL=postgresql+psycopg2://postgres.[PROJECT-REF]:[SENHA]@aws-0-[REGIAO].pooler.supabase.com:6543/postgres
   ```

4. Rode as migrations apontando para o Supabase:

   ```bash
   alembic upgrade head
   python -m scripts.seed
   ```

> As migrations rodam **localmente** (ou na sua máquina/CI), não em runtime na
> Vercel.

---

## 🎨 Build do Tailwind (produção)

Em desenvolvimento o `base.html` usa o **Play CDN** (zero configuração).
Para produção, gere o CSS estático com o Tailwind CLI (binário standalone,
sem Node necessário):

```bash
# baixe o binário em https://github.com/tailwindlabs/tailwindcss/releases
tailwindcss -i app/static/css/input.css -o app/static/css/output.css --minify
```

Depois, no `app/templates/base.html`, remova o `<script src="...cdn.tailwindcss.com">`
e mantenha apenas o `<link rel="stylesheet" href="/static/css/output.css">`.

---

## ☁️ Deploy na Vercel

1. Suba o projeto para um repositório Git e importe-o na Vercel.
2. O `vercel.json` já configura o runtime Python e reescreve todas as rotas para
   `api/index.py`, incluindo os arquivos de `app/` (templates e estáticos).
3. Em **Project → Settings → Environment Variables**, defina:

   | Variável             | Valor                                            |
   | -------------------- | ------------------------------------------------ |
   | `DATABASE_URL`       | string do **pooler** do Supabase (porta 6543)    |
   | `SECRET_KEY`         | chave forte (token_hex)                          |
   | `ADMIN_EMAIL`        | email que será admin                             |
   | `JWT_EXPIRE_MINUTES` | `10080` (7 dias) — opcional                       |
   | `ENVIRONMENT`        | `production` (ativa cookies Secure/HTTPS)        |

4. Antes (ou após) o deploy, rode **uma vez** as migrations e o seed apontando
   para o Supabase de produção (localmente, com o `.env` de produção):

   ```bash
   alembic upgrade head
   python -m scripts.seed
   python -m scripts.create_admin   # cria o admin padrão (ADMIN_EMAIL/ADMIN_PASSWORD)
   ```

5. Faça o deploy. Acesse a URL e entre em `/login` com as credenciais do admin
   padrão para começar a administrar.

---

## 🔐 Segurança

- Senhas com **bcrypt** (limite de 72 bytes tratado).
- Sessão via **JWT** em cookie `httpOnly` + `SameSite=Lax` (+ `Secure` em produção).
- Rotas protegidas por dependencies (`get_current_user`, `require_admin`).
- Validação de formulários com **Pydantic**; autoescape do Jinja2 (anti-XSS);
  queries parametrizadas pelo SQLAlchemy (anti-SQL injection).
- Segredos fora do versionamento (`.gitignore`).

## 🧪 Fases do torneio

`grupos · trinta_e_dois_avos (Round of 32) · oitavas · quartas · semifinal · terceiro · final`

O mata-mata é criado desde o início com **placeholders** (ex.: `1A`, `2B`,
`Venc. Oitavas 1`). O admin define os times reais em **/admin/mata-mata**
conforme a competição avança e abre os palpites.
