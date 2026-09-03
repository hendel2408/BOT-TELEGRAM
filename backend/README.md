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

## Reinicio dos robos GCV

Comando Telegram:

```text
/reiniciar_gcv
/reiniciar_robos
/diagnostico_gcv
```

Variaveis esperadas no `backend/.env`:

```env
GCV_ALLOWED_CHAT_IDS=<ids_dos_grupos_separados_por_virgula>
GCV_EXECUTABLE_PATH=
GCV_ROBO_PASSWORD=
```

Os comandos GCV so funcionam em grupos ou supergrupos cujo `chat.id` esteja em `GCV_ALLOWED_CHAT_IDS`. Conversas privadas e outros grupos ficam bloqueados. Em grupos com topicos/forum, a autorizacao usa o `chat.id` principal do grupo e ignora o `message_thread_id`.

`GCV_EXECUTABLE_PATH` e opcional. Se ela nao for informada, o sistema resolve a Area de Trabalho real do usuario atual pelo Windows Known Folders e procura:

```text
ROBO GCV\csrobogcv (1).exe
```

Se preferir o Gerenciador de Credenciais do Windows, cadastre uma credencial generica com o alvo `BOT_TELEGRAM_GCV_ROBO_PASSWORD`, ou ajuste:

```env
GCV_ROBO_PASSWORD_CREDENTIAL_TARGET=BOT_TELEGRAM_GCV_ROBO_PASSWORD
```

Nao coloque a senha em codigo, logs, prints ou mensagens.

Por padrao, a automacao procura os templates dos atalhos em:

```text
backend\src\bot_app\assets\gcv\parar_robos.png
backend\src\bot_app\assets\gcv\monitorar_robos.png
backend\src\bot_app\assets\gcv\aviso_robos_encerrados.png
backend\src\bot_app\assets\gcv\terminal_parar_robos.png
backend\src\bot_app\assets\gcv\fechar_terminal_parar_robos.png
backend\src\bot_app\assets\gcv\fechar_rdp_normal.png
backend\src\bot_app\assets\gcv\fechar_rdp_normal_servidor.png
backend\src\bot_app\assets\gcv\fechar_rdp_hover.png
backend\src\bot_app\assets\gcv\confirmacao_desconexao_rdp.png
backend\src\bot_app\assets\gcv\ok_desconexao_rdp.png
```

Os templates dos atalhos devem ser recortes limpos feitos dentro da Area de Trabalho Remota maximizada, incluindo o icone e o nome completo do atalho. Nao use recortes com cursor, seta, selecao azul, destaque de hover ou apenas o circulo do icone `CS`, porque os atalhos `Parar Robos` e `Monitorar Robos` usam o mesmo simbolo.

Os templates `aviso_robos_encerrados.png` e `terminal_parar_robos.png` devem ser recortes da barra superior completa de cada janela, incluindo o titulo e o botao `X`. O aviso ainda usa clique calculado relativamente ao template encontrado. O terminal usa `terminal_parar_robos.png` para limitar a busca e depois procura visualmente `fechar_terminal_parar_robos.png` no canto superior direito dele.

Os templates `fechar_rdp_normal.png`, `fechar_rdp_normal_servidor.png` e `fechar_rdp_hover.png` devem ser recortes do botao `X` da barra superior da RDP. Os dois templates normais sao mantidos por padrao para compatibilidade com ambientes diferentes. O template `confirmacao_desconexao_rdp.png` deve conter a janela de confirmacao da desconexao, incluindo a area onde fica o botao `OK`. O template `ok_desconexao_rdp.png` deve conter somente o botao `OK` completo.

As variaveis abaixo sao opcionais e servem apenas para substituir os templates padrao:

```env
GCV_PARAR_ROBOS_IMAGE=backend\src\bot_app\assets\gcv\parar_robos.png
GCV_MONITORAR_ROBOS_IMAGE=backend\src\bot_app\assets\gcv\monitorar_robos.png
GCV_AVISO_ROBOS_ENCERRADOS_IMAGE=backend\src\bot_app\assets\gcv\aviso_robos_encerrados.png
GCV_TERMINAL_PARAR_ROBOS_IMAGE=backend\src\bot_app\assets\gcv\terminal_parar_robos.png
GCV_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE=backend\src\bot_app\assets\gcv\fechar_terminal_parar_robos.png
GCV_FECHAR_RDP_NORMAL_IMAGE=backend\src\bot_app\assets\gcv\fechar_rdp_normal.png;backend\src\bot_app\assets\gcv\fechar_rdp_normal_servidor.png
GCV_FECHAR_RDP_HOVER_IMAGE=backend\src\bot_app\assets\gcv\fechar_rdp_hover.png
GCV_CONFIRMACAO_DESCONEXAO_RDP_IMAGE=backend\src\bot_app\assets\gcv\confirmacao_desconexao_rdp.png
GCV_OK_DESCONEXAO_RDP_IMAGE=backend\src\bot_app\assets\gcv\ok_desconexao_rdp.png
```

Se uma variavel de imagem receber caminho relativo, ele sera resolvido a partir da raiz do projeto. Caminhos absolutos continuam sendo aceitos.

Timeouts opcionais:

```env
GCV_LOGIN_TIMEOUT_S=60
GCV_DESKTOP_TIMEOUT_S=120
GCV_STOP_VISUAL_TIMEOUT_S=15
GCV_VISUAL_POLL_INTERVAL_S=0.5
GCV_MONITORAR_TIMEOUT_S=60
GCV_RDP_REVEAL_BAR_DELAY_S=2
GCV_RDP_CONFIRMATION_TIMEOUT_S=10
GCV_RDP_CLOSE_VERIFY_TIMEOUT_S=10
GCV_RDP_TOP_BAR_SEARCH_HEIGHT=120
GCV_IMAGE_CONFIDENCE=0.86
GCV_IMAGE_MAX_MEAN_DIFF=35
GCV_IMAGE_SCALE_MIN=0.65
GCV_IMAGE_SCALE_MAX=1.50
GCV_IMAGE_SCALE_STEP=0.05
GCV_IMAGE_BASE_RDP_WIDTH=1920
GCV_IMAGE_BASE_RDP_HEIGHT=1080
GCV_IMAGE_SCALE_VARIATIONS=
GCV_AVISO_CLOSE_X_RATIO=0.9597989949748744
GCV_AVISO_CLOSE_Y_RATIO=0.34210526315789475
```

O bot precisa rodar na sessao interativa do mesmo usuario que possui a pasta `ROBO GCV` na Area de Trabalho. Nao execute esta automacao como servico isolado na Session 0.

A funcao GCV controla a tela somente durante a execucao do comando. Mantenha a sessao do Windows desbloqueada enquanto a automacao estiver em andamento. Fora do momento da execucao, a conexao remota nao precisa permanecer aberta ou visivel.

A automacao localiza a janela da conexao remota apos o login e tenta restaura-la/maximiza-la antes do reconhecimento visual. Se o Windows nao confirmar foreground pelo mesmo handle, o fluxo nao e interrompido; a confirmacao passa a ser o template encontrado na captura atual da regiao da RDP. O PyAutoGUI fica reservado para reconhecer e clicar nos elementos graficos dentro da sessao remota.

Apos clicar em `Parar Robos`, a automacao aguarda 10 segundos, procura visualmente a barra do aviso dentro da regiao da Area de Trabalho Remota, clica no X calculado por proporcao dentro do template, aguarda 2 segundos e confirma que o aviso desapareceu. Em seguida, procura visualmente a barra do terminal `Parar Robos`, limita a busca ao canto superior direito dele, localiza visualmente o template do botao X, clica no centro encontrado, aguarda 2 segundos e confirma que o terminal desapareceu. Depois disso ela procura visualmente `Monitorar Robos` e da duplo clique para iniciar novamente. O bot nunca clica no botao `OK` nesse fluxo.

Depois de abrir `Monitorar Robos`, a automacao aguarda 5 segundos, move o mouse para o topo central da tela para revelar a barra superior da RDP, procura visualmente o botao `X` somente na faixa superior da tela, clica no template encontrado e confirma a desconexao pelo botao `OK` localizado dentro da janela de confirmacao. Nao usa `Alt+F4`, `WM_CLOSE`, `SC_CLOSE`, `taskkill` nem coordenadas fixas para encerrar o acesso remoto.

O script `scripts\iniciar_tudo.bat` usa o Python em `.venv\Scripts\python.exe`, valida as dependencias GCV antes de iniciar e sobe o mesmo backend Telegram existente. Ele nao cria bot ou processo separado para GCV.
