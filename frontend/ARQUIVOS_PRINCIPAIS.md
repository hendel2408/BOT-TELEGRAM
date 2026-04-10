# Arquivos Principais do Frontend

Este arquivo resume onde o dev frontend deve mexer.

## Pasta Principal

Tudo do frontend fica em:



## Arquivos Mais Importantes

### Estrutura da aplicacao

- [src/main.tsx](C:/Users/Hendel/Desktop/bot/frontend/src/main.tsx)
  Ponto de entrada da aplicacao React.

- [src/App.tsx](C:/Users/Hendel/Desktop/bot/frontend/src/App.tsx)
  Componente principal da interface.

### Comunicacao com o backend

- [src/api.ts](C:/Users/Hendel/Desktop/bot/frontend/src/api.ts)
  Centraliza as chamadas HTTP para a API do backend.

### Tipagem

- [src/types.ts](C:/Users/Hendel/Desktop/bot/frontend/src/types.ts)
  Tipos TypeScript usados no frontend.

### Utilitarios

- [src/utils/labels.js](C:/Users/Hendel/Desktop/bot/frontend/src/utils/labels.js)
  Textos auxiliares, labels e tons de status.

### Estilo

- [src/styles/app.css](C:/Users/Hendel/Desktop/bot/frontend/src/styles/app.css)
  Estilos principais da interface.

### Configuracao do projeto

- [package.json](C:/Users/Hendel/Desktop/bot/frontend/package.json)
  Scripts e dependencias do frontend.

- [vite.config.ts](C:/Users/Hendel/Desktop/bot/frontend/vite.config.ts)
  Configuracao do Vite e proxy para o backend.

- [tsconfig.json](C:/Users/Hendel/Desktop/bot/frontend/tsconfig.json)
  Configuracao do TypeScript.

- [index.html](C:/Users/Hendel/Desktop/bot/frontend/index.html)
  HTML base usado pelo Vite.

## Onde Mexer em Cada Caso

Se quiser mudar layout, cards, formularios e estrutura visual:

- `src/App.tsx`
- `src/styles/app.css`

Se quiser mudar nomes, textos e status:

- `src/utils/labels.js`

Se quiser mudar dados enviados ou lidos da API:

- `src/api.ts`
- `src/types.ts`

Se quiser mudar build, porta do frontend ou proxy:

- `vite.config.ts`
- `package.json`

## Fluxo Basico

Rodar frontend:

```powershell
cd C:\Users\Hendel\Desktop\bot\frontend
npm install
npm run dev
```

Gerar build:

```powershell
cd C:\Users\Hendel\Desktop\bot\frontend
npm run build
```
