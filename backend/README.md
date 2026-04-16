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

## Selenium (ChromeDriver)

Se aparecer erro `Unable to obtain driver for chrome`, configure no `backend/.env`:

```env
CHROMEDRIVER_PATH=C:\caminho\para\chromedriver.exe
CHROME_BINARY_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
```

`CHROME_BINARY_PATH` e opcional. `CHROMEDRIVER_PATH` so e necessario quando o Selenium Manager nao consegue localizar/baixar o driver automaticamente.
