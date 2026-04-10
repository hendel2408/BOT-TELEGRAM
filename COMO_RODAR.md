# Como Rodar

Este projeto esta dividido em duas partes:

- `backend/`: API, automacoes, bot e arquivos de dados
- `frontend/`: interface web em React + TypeScript

## Antes de Rodar

Confira estes pontos primeiro:

1. Tenha Python instalado.
2. Tenha Node.js e npm instalados.
3. Tenha a pasta `venv/` funcionando na raiz do projeto.
4. Tenha o arquivo `backend/.env` preenchido com as variaveis necessarias.
5. Se for usar o frontend buildado pelo backend, gere o build antes com `npm run build`.

## Estrutura Esperada

Na raiz do projeto voce deve ter:

- `backend/`
- `frontend/`
- `scripts/`
- `venv/`

## Backend

Ative o ambiente virtual na raiz:

```powershell
cd C:\Users\Hendel\Desktop\bot
.\venv\Scripts\Activate.ps1
```

Rodar so o painel:

```powershell
python backend\app.py
```

Rodar painel + bot:

```powershell
python backend\main.py
```

Atalho por `.bat`:

```powershell
.\scripts\iniciar_painel.bat
.\scripts\iniciar_tudo.bat
```

## Frontend

Entre na pasta do frontend:

```powershell
cd C:\Users\Hendel\Desktop\bot\frontend
```

Instale as dependencias:

```powershell
npm install
```

Rodar em desenvolvimento:

```powershell
npm run dev
```

Build para producao:

```powershell
npm run build
```

## Como Usar em Desenvolvimento

O fluxo mais seguro e este:

Terminal 1, backend:

```powershell
cd C:\Users\Hendel\Desktop\bot
.\venv\Scripts\Activate.ps1
python backend\app.py
```

Terminal 2, frontend:

```powershell
cd C:\Users\Hendel\Desktop\bot\frontend
npm install
npm run dev
```

Abra no navegador:

```text
http://localhost:5173
```

Nesse modo, o Vite faz proxy para o backend em `http://127.0.0.1:5000`.

## Como Usar Sem Vite

Se quiser rodar tudo pelo backend:

1. Gere o build do frontend:

```powershell
cd C:\Users\Hendel\Desktop\bot\frontend
npm run build
```

2. Suba o backend:

```powershell
cd C:\Users\Hendel\Desktop\bot
.\venv\Scripts\Activate.ps1
python backend\app.py
```

3. Abra:

```text
http://127.0.0.1:5000
```

## O Que Fazer Antes de Entregar ou Testar

- Confirmar que `backend/.env` existe e esta correto.
- Confirmar que o `venv` esta ativado.
- Confirmar que `frontend/node_modules` foi instalado.
- Rodar `npm run build` se o backend for servir o frontend.
- Se o frontend mudou API, alinhar antes com o backend.

## Problemas Comuns

`python: can't open file`

- Voce provavelmente esta rodando o comando da pasta errada.
- Rode a partir da raiz do projeto ou use os caminhos mostrados acima.

`ModuleNotFoundError`

- O `venv` pode nao estar ativado.
- Pode estar usando Python global em vez do Python da `venv`.

`npm run dev` abre, mas a tela nao carrega dados

- O backend provavelmente nao esta rodando na porta `5000`.

`python backend\app.py` abre, mas a interface nao aparece

- Rode antes:

```powershell
cd frontend
npm run build
```

## Resumo Rapido

Desenvolvimento:

- backend: `python backend\app.py`
- frontend: `cd frontend` + `npm run dev`

Uso local simples:

- `cd frontend` + `npm run build`
- `python backend\app.py`
