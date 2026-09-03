# Templates GCV

Coloque nesta pasta os templates padrao usados pela automacao:

- `parar_robos.png`
- `monitorar_robos.png`
- `aviso_robos_encerrados.png`
- `terminal_parar_robos.png`
- `fechar_rdp_normal.png`
- `fechar_rdp_hover.png`
- `confirmacao_desconexao_rdp.png`
- `ok_desconexao_rdp.png`

Os atalhos `parar_robos.png` e `monitorar_robos.png` devem incluir o icone e o
nome completo. Nao use recortes com cursor, seta, selecao azul, destaque de hover
ou apenas o circulo do icone `CS`, porque os dois atalhos usam o mesmo simbolo.

Os templates `aviso_robos_encerrados.png` e `terminal_parar_robos.png` devem ser
recortes da barra superior completa de cada janela, incluindo o titulo e o botao
`X`.

Os templates `fechar_rdp_normal.png` e `fechar_rdp_hover.png` devem ser recortes
do botao `X` da barra superior da RDP. O template
`confirmacao_desconexao_rdp.png` deve conter a janela de confirmacao da
desconexao, incluindo a area onde fica o botao `OK`. O template
`ok_desconexao_rdp.png` deve conter somente o botao `OK` completo.

As variaveis `GCV_PARAR_ROBOS_IMAGE`, `GCV_MONITORAR_ROBOS_IMAGE`,
`GCV_AVISO_ROBOS_ENCERRADOS_IMAGE`, `GCV_TERMINAL_PARAR_ROBOS_IMAGE`,
`GCV_FECHAR_RDP_NORMAL_IMAGE`, `GCV_FECHAR_RDP_HOVER_IMAGE`,
`GCV_CONFIRMACAO_DESCONEXAO_RDP_IMAGE` e `GCV_OK_DESCONEXAO_RDP_IMAGE` no
`backend/.env` sao opcionais e servem apenas para substituir estes arquivos
padrao.
