# 🚀 Guia Rápido Git (2 PCs + Servidor)

## 📥 Antes de começar a trabalhar (QUALQUER PC)

```bash
git pull
```

---

## 📤 Depois de fazer alterações

```bash
git add .
git commit -m "descrição do que foi feito"
git push
```

---

## 🔄 Primeiro uso em outro PC (clone)

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

---

## ⚠️ Se `git pull` der erro de branch

```bash
git branch --set-upstream-to=origin/main main
```

---

## 💥 Forçar atualização (APAGA alterações locais)

```bash
git fetch
git reset --hard origin/main
```

---

## 🔍 Verificar status

```bash
git status
```

---

## 🧠 Regras de Ouro

* Sempre dar `git pull` antes de começar
* Sempre dar `git push` depois de terminar
* Nunca usar `reset --hard` sem ter certeza
