# Backend

Backend Python do projeto.

## Estrutura

- `src/`: codigo-fonte Python
- `data/`: banco SQLite e arquivos gerados em runtime
- `app.py`: entrypoint do painel web
- `main.py`: entrypoint do painel + bot
- `.env`: configuracao local do backend

## Como rodar

Painel:

```powershell
python backend\app.py
```

Painel + bot:

```powershell
python backend\main.py
```
