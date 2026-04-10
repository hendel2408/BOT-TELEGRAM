# Estrutura do Codigo

Este arquivo explica a funcao dos arquivos principais do projeto.

O objetivo e ajudar no aprendizado: entender o que cada parte faz, quais arquivos sao essenciais e quais arquivos sao apenas suporte ou gerados automaticamente.

## Visao Geral

O projeto esta dividido em 3 blocos:

- `backend/`: Python, automacoes, API, bot e dados
- `frontend/`: interface web em React + TypeScript
- `scripts/`: atalhos `.bat` para iniciar o projeto

## Arquivos da Raiz

### [COMO_RODAR.md](C:/Users/Hendel/Desktop/bot/COMO_RODAR.md)

Guia de execucao do projeto.

Serve para:

- explicar o que instalar antes
- mostrar como rodar backend e frontend
- mostrar o fluxo com um ou dois terminais

### [ESTRUTURA_DO_CODIGO.md](C:/Users/Hendel/Desktop/bot/ESTRUTURA_DO_CODIGO.md)

Este arquivo.

Serve para:

- explicar a funcao de cada arquivo importante
- ajudar quem esta estudando o projeto

### [pyrightconfig.json](C:/Users/Hendel/Desktop/bot/pyrightconfig.json)

Configuracao do analisador Python do VS Code.

Serve para:

- fazer o Pylance encontrar os imports do backend
- reduzir avisos falsos no editor

Nao participa da execucao do sistema em producao.

## Pasta `scripts/`

### [scripts/iniciar_painel.bat](C:/Users/Hendel/Desktop/bot/scripts/iniciar_painel.bat)

Atalho para abrir apenas o painel web.

Ele:

- encontra a pasta do projeto
- valida o Python da `venv`
- executa `backend/app.py`

### [scripts/iniciar_tudo.bat](C:/Users/Hendel/Desktop/bot/scripts/iniciar_tudo.bat)

Atalho para abrir painel + bot.

Ele:

- encontra a pasta do projeto
- valida o Python da `venv`
- executa `backend/main.py`

## Pasta `backend/`

Esta e a parte Python do projeto.

Ela contem:

- a API web
- o bot do Telegram
- as automacoes Selenium
- o armazenamento de historico
- a fila de execucao

### Arquivos de entrada do backend

#### [backend/app.py](C:/Users/Hendel/Desktop/bot/backend/app.py)

Entry point simples do painel web.

Funcao:

- ajusta o caminho do `src`
- importa o painel real
- executa o servidor web

Use este arquivo quando quiser rodar so a parte web.

#### [backend/main.py](C:/Users/Hendel/Desktop/bot/backend/main.py)

Entry point do sistema completo.

Funcao:

- ajusta o caminho do `src`
- importa a aplicacao principal
- executa painel + bot

Use este arquivo quando quiser rodar tudo.

#### [backend/README.md](C:/Users/Hendel/Desktop/bot/backend/README.md)

Resumo rapido do backend.

Funcao:

- mostrar a estrutura da pasta
- lembrar os comandos principais

#### [backend/.env](C:/Users/Hendel/Desktop/bot/backend/.env)

Arquivo de configuracao local.

Funcao:

- guardar tokens, usuarios, senhas e configuracoes sensiveis

Importante:

- este arquivo e essencial para o backend funcionar direito
- normalmente nao deve ser enviado para outras pessoas com segredos reais

#### [backend/requirements-web.txt](C:/Users/Hendel/Desktop/bot/backend/requirements-web.txt)

Lista de dependencias Python.

Funcao:

- registrar bibliotecas usadas pelo backend

### Pasta `backend/data/`

Guarda arquivos gerados durante a execucao.

#### [backend/data/historico.db](C:/Users/Hendel/Desktop/bot/backend/data/historico.db)

Banco SQLite do projeto.

Funcao:

- salvar historico das automacoes
- manter registro de execucoes

#### [backend/data/ip_livre.txt](C:/Users/Hendel/Desktop/bot/backend/data/ip_livre.txt)

Arquivo de apoio da automacao BluePex.

Funcao:

- registrar o ultimo IP livre encontrado

### Pasta `backend/src/bot_app/`

Aqui fica o codigo-fonte principal do backend.

#### [backend/src/bot_app/main.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/main.py)

Modulo principal da aplicacao Python.

Funcao:

- sobe o painel em uma thread separada
- executa o bot do Telegram no processo principal

Em outras palavras:

- coordena o backend completo

#### [backend/src/bot_app/telegram_bot.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/telegram_bot.py)

Implementa o bot do Telegram.

Funcao:

- carregar token do `.env`
- registrar comandos do bot
- receber pedidos do Telegram
- enviar pedidos para a fila de execucao
- devolver resposta ao usuario

Este arquivo e importante porque conecta o mundo externo do Telegram ao sistema interno.

#### [backend/src/bot_app/__init__.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/__init__.py)

Marca `bot_app` como pacote Python.

Funcao:

- permitir imports como `from bot_app.main import ...`

### Pasta `backend/src/bot_app/web/`

Contem a camada web do backend.

#### [backend/src/bot_app/web/panel.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/web/panel.py)

Este e um dos arquivos mais importantes do projeto.

Funcao:

- criar a aplicacao Flask
- expor as rotas da API
- servir o frontend buildado
- receber requisicoes do frontend
- enviar os trabalhos para a fila

Rotas principais:

- `GET /`: entrega o frontend
- `GET /api/status`: devolve status atual, fila e historico
- `POST /jobs/bluepex`: cria um job BluePex
- `POST /jobs/consultor`: cria um job de consultor
- `GET /healthz`: rota simples de saude

#### [backend/src/bot_app/web/__init__.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/web/__init__.py)

Marca a pasta `web` como pacote Python.

### Pasta `backend/src/bot_app/services/`

Contem servicos internos reutilizaveis.

#### [backend/src/bot_app/services/history_store.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/services/history_store.py)

Servico de historico.

Funcao:

- criar a tabela do banco SQLite
- salvar entradas de historico
- buscar historico recente

Este arquivo cuida da persistencia dos eventos do sistema.

#### [backend/src/bot_app/services/job_queue.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/services/job_queue.py)

Servico de fila de automacoes.

Funcao:

- criar e controlar a fila
- manter um job por vez em execucao
- iniciar worker em background
- esperar o job terminar
- registrar resultado no historico

Este arquivo e muito importante para evitar que varias automacoes rodem ao mesmo tempo e se atrapalhem.

#### [backend/src/bot_app/services/__init__.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/services/__init__.py)

Marca a pasta `services` como pacote Python.

### Pasta `backend/src/bot_app/automations/`

Contem as automacoes Selenium.

#### [backend/src/bot_app/automations/bluepex.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/automations/bluepex.py)

Automacao do BluePex.

Funcao:

- fazer login no sistema BluePex
- procurar IP livre
- preencher formulario de liberacao
- aplicar as mudancas
- devolver resultado da operacao

Este arquivo contem a logica mais operacional da liberacao BluePex.

#### [backend/src/bot_app/automations/consultor_cs.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/automations/consultor_cs.py)

Automacao do sistema de consultores.

Funcao:

- fazer login no sistema CS
- navegar ate a tela correta
- pesquisar o consultor
- preencher permissao e data limite
- processar a liberacao

#### [backend/src/bot_app/automations/__init__.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/automations/__init__.py)

Marca a pasta `automations` como pacote Python.

### Pasta `backend/src/bot_app/common/`

Contem utilitarios compartilhados.

#### [backend/src/bot_app/common/paths.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/common/paths.py)

Arquivo central de caminhos do projeto.

Funcao:

- definir onde fica o backend
- definir onde fica o frontend
- apontar para `.env`
- apontar para `data/`
- apontar para `frontend/dist`

Este arquivo e importante porque reduz dependencias de caminho espalhadas no projeto.

#### [backend/src/bot_app/common/__init__.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/common/__init__.py)

Marca a pasta `common` como pacote Python.

## Pasta `frontend/`

Esta e a parte visual do sistema.

Ela contem:

- a interface
- os estilos
- a comunicacao HTTP com o backend
- o processo de build

### Arquivos principais do frontend

#### [frontend/package.json](C:/Users/Hendel/Desktop/bot/frontend/package.json)

Arquivo central do frontend.

Funcao:

- listar dependencias do frontend
- definir scripts como `npm run dev` e `npm run build`

#### [frontend/package-lock.json](C:/Users/Hendel/Desktop/bot/frontend/package-lock.json)

Trava versoes exatas das dependencias.

Funcao:

- garantir instalacoes mais previsiveis

#### [frontend/vite.config.ts](C:/Users/Hendel/Desktop/bot/frontend/vite.config.ts)

Configuracao do Vite.

Funcao:

- definir servidor de desenvolvimento
- definir proxy para o backend
- controlar o build do frontend

#### [frontend/tsconfig.json](C:/Users/Hendel/Desktop/bot/frontend/tsconfig.json)

Configuracao do TypeScript.

Funcao:

- definir regras de compilacao e checagem

#### [frontend/index.html](C:/Users/Hendel/Desktop/bot/frontend/index.html)

HTML base da aplicacao.

Funcao:

- criar o elemento raiz onde o React monta a interface

#### [frontend/README.md](C:/Users/Hendel/Desktop/bot/frontend/README.md)

Guia rapido da pasta frontend.

#### [frontend/ARQUIVOS_PRINCIPAIS.md](C:/Users/Hendel/Desktop/bot/frontend/ARQUIVOS_PRINCIPAIS.md)

Resumo dos arquivos que o dev frontend deve alterar.

### Pasta `frontend/src/`

Aqui fica o codigo do frontend.

#### [frontend/src/main.tsx](C:/Users/Hendel/Desktop/bot/frontend/src/main.tsx)

Ponto de entrada do React.

Funcao:

- importar estilos
- importar o componente principal
- montar a aplicacao no elemento `#root`

#### [frontend/src/App.tsx](C:/Users/Hendel/Desktop/bot/frontend/src/App.tsx)

Arquivo principal da interface.

Funcao:

- montar a tela principal
- exibir formulários
- mostrar status, fila e historico
- buscar dados do backend
- enviar requisicoes de BluePex e Consultor

Este e um dos arquivos mais importantes do frontend.

#### [frontend/src/api.ts](C:/Users/Hendel/Desktop/bot/frontend/src/api.ts)

Camada de comunicacao com a API.

Funcao:

- chamar `GET /api/status`
- chamar `POST /jobs/bluepex`
- chamar `POST /jobs/consultor`

Esse arquivo separa a interface visual da logica de requisicao HTTP.

#### [frontend/src/types.ts](C:/Users/Hendel/Desktop/bot/frontend/src/types.ts)

Tipos TypeScript do frontend.

Funcao:

- tipar jobs
- tipar estado da aplicacao
- tipar respostas da API

Ajuda no aprendizado porque mostra claramente a estrutura dos dados.

#### [frontend/src/vite-env.d.ts](C:/Users/Hendel/Desktop/bot/frontend/src/vite-env.d.ts)

Declaracoes de tipo do ambiente Vite.

Funcao:

- ajudar o TypeScript a entender o ambiente do frontend

#### [frontend/src/utils/labels.js](C:/Users/Hendel/Desktop/bot/frontend/src/utils/labels.js)

Utilitarios pequenos de texto e status.

Funcao:

- traduzir tipo de job em label amigavel
- decidir o tom visual do status
- gerar textos resumidos

#### [frontend/src/styles/app.css](C:/Users/Hendel/Desktop/bot/frontend/src/styles/app.css)

Arquivo principal de estilo.

Funcao:

- definir cores
- definir layout
- estilizar cards, formularios, fila e historico

## Arquivos Gerados Automaticamente

Esses arquivos existem, mas normalmente nao sao o foco do estudo:

### `frontend/dist/`

Contem o frontend compilado.

Funcao:

- ser servido pelo backend em producao/local buildado

Voce normalmente nao edita esse codigo manualmente.

### `frontend/node_modules/`

Contem dependencias instaladas pelo npm.

Funcao:

- permitir o funcionamento do frontend

Tambem nao e onde se estuda a logica do projeto.

### `__pycache__/`

Arquivos gerados pelo Python.

Funcao:

- cache de bytecode

Tambem nao faz parte da logica do projeto.

## Arquivos Mais Essenciais Para Entender o Projeto

Se voce quiser estudar o projeto na ordem certa, comece por estes:

1. [backend/src/bot_app/web/panel.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/web/panel.py)
2. [backend/src/bot_app/services/job_queue.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/services/job_queue.py)
3. [backend/src/bot_app/services/history_store.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/services/history_store.py)
4. [backend/src/bot_app/telegram_bot.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/telegram_bot.py)
5. [backend/src/bot_app/automations/bluepex.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/automations/bluepex.py)
6. [backend/src/bot_app/automations/consultor_cs.py](C:/Users/Hendel/Desktop/bot/backend/src/bot_app/automations/consultor_cs.py)
7. [frontend/src/App.tsx](C:/Users/Hendel/Desktop/bot/frontend/src/App.tsx)
8. [frontend/src/api.ts](C:/Users/Hendel/Desktop/bot/frontend/src/api.ts)
9. [frontend/src/types.ts](C:/Users/Hendel/Desktop/bot/frontend/src/types.ts)

## Resumo Didatico

Em uma frase por area:

- `panel.py`: recebe requisicoes e expõe a API
- `job_queue.py`: organiza a fila de automacoes
- `history_store.py`: salva e consulta historico
- `telegram_bot.py`: conecta Telegram ao sistema
- `bluepex.py` e `consultor_cs.py`: executam automacoes reais
- `App.tsx`: desenha a interface
- `api.ts`: conversa com o backend
- `types.ts`: define o formato dos dados
- `app.css`: define o visual
