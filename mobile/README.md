# 📱 Bolão Arianjo — App Mobile (React Native / Expo)

App mobile do **Bolão da Copa do Mundo Arianjo**. Consome a **API REST** do
backend (FastAPI na nuvem/Vercel) e usa o **sensor acelerômetro** do aparelho.

Faz parte do projeto de **Sistemas Distribuídos e Mobile** — é o cliente móvel
da arquitetura distribuída (ver diagrama em `../ARQUITETURA.md`).

## O que o app faz

- **Login / Cadastro** (autenticação por **JWT Bearer token**, salvo no aparelho).
- **Jogos**: lista todas as partidas por fase e permite **registrar/editar palpites**
  (CRUD no banco na nuvem via API). No mata-mata, se o palpite for empate, aparece
  **"Quem avança?"**.
- **Ranking** geral, com destaque para você.
- **Histórico** de jogos finalizados, com seu palpite e pontos.
- **Sensor (acelerômetro):** **chacoalhe o celular para atualizar** os dados
  (também há "puxar para atualizar").

## Pré-requisitos

- Node.js 18+
- App **Expo Go** no celular (Android/iOS) — ou um emulador.

## Como rodar

```bash
cd mobile
npm install
# se houver aviso de versões, alinhe com o SDK do Expo:
#   npx expo install --fix
npx expo start
```

Abra o **Expo Go** no celular e escaneie o QR code. O app já aponta para a API
de produção, então **funciona de imediato** (não precisa subir o backend).

> Para apontar para um backend local, edite `src/config.js` e use o **IP da sua
> máquina** (não `localhost`), pois o celular não enxerga o localhost do PC.

## Estrutura

```
mobile/
  App.js                      navegação (auth stack / tabs) + AuthProvider
  src/
    config.js                 URL da API
    api/client.js             fetch + Bearer token (AsyncStorage)
    context/AuthContext.js    estado de login (login/cadastro/logout)
    hooks/useShake.js         SENSOR acelerômetro (chacoalhar p/ atualizar)
    components/JogoCard.js     cartão de palpite (+ "quem avança")
    screens/                  Login, Cadastro, Jogos, Ranking, Histórico
    theme.js                  cores
```

## Como o sensor é usado

`src/hooks/useShake.js` assina o **Accelerometer** (`expo-sensors`), calcula a
magnitude do vetor de aceleração (≈1g em repouso) e, ao detectar um pico acima
do limite (chacoalhada), dispara o recarregamento dos dados via API. Isso atende
ao requisito de **coleta de dados através de um sensor do dispositivo móvel**.
