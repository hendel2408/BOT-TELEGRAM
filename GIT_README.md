# Git Readme
lllll
Este arquivo explica o fluxo de Git usado neste projeto.

Objetivo:

- programar em um PC
- subir as alteracoes para o GitHub
- ir para outro PC
- puxar as alteracoes e sobrescrever os arquivos locais versionados

## Ideia Simples

O Git sera usado como fonte principal do codigo.

Fluxo:

1. voce altera arquivos no notebook
2. faz `commit` e `push`
3. no outro PC, baixa as atualizacoes do GitHub
4. os arquivos versionados locais sao sobrescritos pelos do GitHub

## Antes de Tudo

Nos dois PCs, voce precisa ter:

- `git` instalado
- acesso ao repositorio no GitHub

Se o repositorio for privado, pode ser necessario fazer login no GitHub na primeira vez.

## Enviar Alteracoes Para o GitHub

No PC onde voce editou o projeto:

```powershell
cd C:\caminho\do\projeto
git add .
git commit -m "Descreva a alteracao"
git push
```

### O que cada comando faz

`git add .`

- prepara os arquivos alterados para entrar no proximo commit

`git commit -m "mensagem"`

- cria um pacote de alteracoes com uma mensagem

`git push`

- envia esses commits para o GitHub

## Atualizar o Outro PC

No outro PC, dentro da pasta do projeto:

```powershell
cd C:\caminho\do\projeto
git fetch origin
git reset --hard origin/main
```

### O que cada comando faz

`git fetch origin`

- baixa do GitHub as informacoes mais recentes

`git reset --hard origin/main`

- faz a copia local ficar igual ao que esta no GitHub na branch `main`
- sobrescreve os arquivos versionados locais

## Quando Usar `git clean -fd`

Se voce quiser tambem apagar arquivos locais extras que nao estao no Git:

```powershell
git clean -fd
```

Esse comando:

- remove arquivos e pastas nao rastreados pelo Git

### Importante

Arquivos ignorados pelo `.gitignore` normalmente nao sao apagados por esse comando.

Neste projeto, isso ajuda a preservar coisas como:

- `backend/.env`
- `backend/data/`
- `venv/`
- `frontend/node_modules/`
- `frontend/dist/`

## Fluxo Padrao Deste Projeto

### No notebook

```powershell
git add .
git commit -m "Atualizacao do frontend"
git push
```

### No servidor ou no outro PC

```powershell
git fetch origin
git reset --hard origin/main
```

Se quiser limpeza extra:

```powershell
git clean -fd
```

## Quando Esse Metodo e Bom

Esse metodo e bom quando:

- o outro PC nao e usado para desenvolver ao mesmo tempo
- ele serve mais para executar ou receber atualizacoes
- voce quer sobrescrever rapidamente os arquivos locais com a versao do GitHub

## Cuidado

`git reset --hard origin/main` apaga alteracoes locais nao commitadas em arquivos versionados.

Ou seja:

- se voce mudou um arquivo local e ainda nao commitou
- esse arquivo sera sobrescrito

Se houver algo importante localmente, salve antes.

## Resumo Rapido

Enviar para o GitHub:

```powershell
git add .
git commit -m "Minha alteracao"
git push
```

Puxar no outro PC e sobrescrever os arquivos versionados:

```powershell
git fetch origin
git reset --hard origin/main
```
