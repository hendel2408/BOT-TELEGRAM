import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  fetchAuthState,
  fetchStatus,
  loginPainel,
  logoutPainel,
  submitBluepex,
  submitConsultor
} from "./api";
import type { JobItem, Notice, StatusState } from "./types";
import { resolveStatusTone, resolveTypeLabel, summarizeJob } from "./utils/labels.js";

function Field(props: {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: "text" | "password";
}) {
  const { label, name, value, onChange, placeholder, type = "text" } = props;

  return (
    <label className="field" htmlFor={name}>
      <span>{label}</span>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function NoticeStack({ notices }: { notices: Notice[] }) {
  if (!notices.length) {
    return null;
  }

  return (
    <div className="notice-stack">
      {notices.map((notice) => (
        <div className={`notice ${notice.level}`} key={notice.id}>
          {notice.text}
        </div>
      ))}
    </div>
  );
}

function JobDetails({ job }: { job: JobItem | null }) {
  if (!job) {
    return <p className="empty">Nenhuma automacao em execucao.</p>;
  }

  const entries: Array<[string, string]> = [
    ["Tipo", resolveTypeLabel(job.tipo)],
    ["Origem", job.origem || "-"],
    ["Status", job.status || "-"],
    ["Inicio", job.inicio_humano || "-"],
    ["Mensagem", job.mensagem || "-"]
  ];

  Object.entries(job.dados || {}).forEach(([key, value]) => {
    entries.push([key, String(value ?? "-")]);
  });

  return (
    <div className="detail-list">
      {entries.map(([label, value]) => (
        <div className="tile" key={label}>
          <strong>{label}</strong>
          <p>{value}</p>
        </div>
      ))}
    </div>
  );
}

function QueueList({ items }: { items: JobItem[] }) {
  if (!items.length) {
    return <p className="empty">Nenhum item aguardando na fila.</p>;
  }

  return (
    <div className="list-grid">
      {items.map((item, index) => (
        <article className="tile" key={item.id}>
          <header>
            <strong>{resolveTypeLabel(item.tipo)}</strong>
            <span className="badge">Posicao {index + 1}</span>
          </header>
          <p>Origem: {item.origem || "-"}</p>
          <p>Dados: {JSON.stringify(item.dados || {})}</p>
        </article>
      ))}
    </div>
  );
}

function HistoryList({ items }: { items: JobItem[] }) {
  if (!items.length) {
    return <p className="empty">Nenhuma execucao registrada.</p>;
  }

  return (
    <div className="list-grid">
      {items.map((item) => {
        const detalhe = item.resultado?.ip ? `IP ${item.resultado.ip}` : item.mensagem || "-";

        return (
          <article className="tile" key={item.id}>
            <header>
              <strong>{resolveTypeLabel(item.tipo)}</strong>
              <span>{item.fim_humano || item.inicio_humano || "-"}</span>
            </header>
            <p>Status: {item.status}</p>
            <p>Origem: {item.origem || "-"}</p>
            <p>Detalhe: {detalhe}</p>
          </article>
        );
      })}
    </div>
  );
}

const EMPTY_STATE: StatusState = {
  ocupado: false,
  job_atual: null,
  fila: [],
  historico: []
};

export function App() {
  const [state, setState] = useState<StatusState>(EMPTY_STATE);
  const [booting, setBooting] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authUser, setAuthUser] = useState<string | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [isSendingBluepex, setIsSendingBluepex] = useState(false);
  const [isSendingConsultor, setIsSendingConsultor] = useState(false);
  const [isLogging, setIsLogging] = useState(false);
  const [bluepexNome, setBluepexNome] = useState("");
  const [bluepexMac, setBluepexMac] = useState("");
  const [consultorNome, setConsultorNome] = useState("");
  const [consultorData, setConsultorData] = useState("");
  const [login, setLogin] = useState("");
  const [senha, setSenha] = useState("");

  const statusLabel = useMemo(() => summarizeJob(state.job_atual), [state.job_atual]);
  const statusTone = useMemo(() => resolveStatusTone(state.job_atual), [state.job_atual]);

  function pushNotice(text: string, level: Notice["level"]) {
    const notice: Notice = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      text,
      level
    };

    setNotices((current) => [notice, ...current].slice(0, 4));
    window.setTimeout(() => {
      setNotices((current) => current.filter((item) => item.id !== notice.id));
    }, 4500);
  }

  async function carregarStatusAtual() {
    const payload = await fetchStatus();
    setState(payload);
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        const auth = await fetchAuthState();

        if (!active) {
          return;
        }

        setIsAuthenticated(Boolean(auth.authenticated));
        setAuthUser(auth.user || null);

        if (auth.authenticated) {
          await carregarStatusAtual();
        }
      } catch (error) {
        if (active) {
          pushNotice(error instanceof Error ? error.message : "Falha ao iniciar painel.", "erro");
        }
      } finally {
        if (active) {
          setBooting(false);
        }
      }
    }

    bootstrap();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      return undefined;
    }

    let active = true;

    const timer = window.setInterval(async () => {
      try {
        const payload = await fetchStatus();

        if (active) {
          setState(payload);
        }
      } catch {
        if (active) {
          setIsAuthenticated(false);
          setAuthUser(null);
          setState(EMPTY_STATE);
        }
      }
    }, 2200);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [isAuthenticated]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLogging(true);

    try {
      const response = await loginPainel(login.trim(), senha);
      setIsAuthenticated(Boolean(response.authenticated));
      setAuthUser(response.user || null);
      setSenha("");
      await carregarStatusAtual();
      pushNotice(response.message || "Login realizado.", "ok");
    } catch (error) {
      pushNotice(error instanceof Error ? error.message : "Falha ao autenticar.", "erro");
    } finally {
      setIsLogging(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutPainel();
    } catch {
      // ignora erro de logout e limpa estado local
    }

    setState(EMPTY_STATE);
    setIsAuthenticated(false);
    setAuthUser(null);
    setLogin("");
    setSenha("");
    pushNotice("Sessao encerrada.", "aviso");
  }

  async function handleBluepexSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSendingBluepex(true);

    try {
      const response = await submitBluepex(bluepexNome.trim(), bluepexMac.trim());

      if (response.state) {
        setState(response.state);
      }

      setBluepexNome("");
      setBluepexMac("");
      pushNotice(response.message, response.level || "ok");
    } catch (error) {
      pushNotice(error instanceof Error ? error.message : "Falha ao iniciar BluePex.", "erro");
    } finally {
      setIsSendingBluepex(false);
    }
  }

  async function handleConsultorSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSendingConsultor(true);

    try {
      const response = await submitConsultor(consultorNome.trim(), consultorData.trim());

      if (response.state) {
        setState(response.state);
      }

      setConsultorNome("");
      setConsultorData("");
      pushNotice(response.message, response.level || "ok");
    } catch (error) {
      pushNotice(error instanceof Error ? error.message : "Falha ao iniciar consultor.", "erro");
    } finally {
      setIsSendingConsultor(false);
    }
  }

  if (booting) {
    return <div className="loading-state">Carregando painel...</div>;
  }

  if (!isAuthenticated) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="kicker">Acesso restrito</p>
          <h1>Painel de automacoes</h1>
          <p>Informe login e senha para entrar.</p>
          <NoticeStack notices={notices} />
          <form className="auth-form" onSubmit={handleLogin}>
            <Field
              label="Login"
              name="login"
              value={login}
              onChange={setLogin}
              placeholder="Seu usuario"
            />
            <Field
              label="Senha"
              name="senha"
              value={senha}
              onChange={setSenha}
              placeholder="Sua senha"
              type="password"
            />
            <button className="cta" disabled={isLogging} type="submit">
              {isLogging ? "Entrando..." : "Entrar no painel"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="kicker">Painel operacional</p>
          <h1>Execucao de automacoes</h1>
        </div>
        <div className="topbar-meta">
          <span className={`status-pill ${statusTone}`}>{statusLabel}</span>
          <span className="badge">Fila: {state.fila.length}</span>
          <span className="badge">Historico: {state.historico.length}</span>
          <span className="badge">Usuario: {authUser || "-"}</span>
          <button className="ghost" type="button" onClick={handleLogout}>
            Sair
          </button>
        </div>
      </header>

      <NoticeStack notices={notices} />

      <section className="panel-grid">
        <article className="panel">
          <header>
            <h2>Nova execucao</h2>
            <p>Envio manual para as duas automacoes.</p>
          </header>
          <div className="two-col">
            <form className="job-form" onSubmit={handleBluepexSubmit}>
              <h3>BluePex</h3>
              <Field
                label="Nome do visitante"
                name="bluepex-nome"
                value={bluepexNome}
                onChange={setBluepexNome}
                placeholder="Ex.: Visitante TI"
              />
              <Field
                label="MAC"
                name="bluepex-mac"
                value={bluepexMac}
                onChange={setBluepexMac}
                placeholder="AA:BB:CC:DD:EE:FF"
              />
              <button className="cta" disabled={isSendingBluepex} type="submit">
                {isSendingBluepex ? "Enviando..." : "Executar BluePex"}
              </button>
            </form>

            <form className="job-form" onSubmit={handleConsultorSubmit}>
              <h3>Consultor</h3>
              <Field
                label="Nome do consultor"
                name="consultor-nome"
                value={consultorNome}
                onChange={setConsultorNome}
                placeholder="Ex.: CSCELSO"
              />
              <Field
                label="Data limite"
                name="consultor-data"
                value={consultorData}
                onChange={setConsultorData}
                placeholder="DD/MM/AAAA"
              />
              <button className="cta" disabled={isSendingConsultor} type="submit">
                {isSendingConsultor ? "Enviando..." : "Executar Consultor"}
              </button>
            </form>
          </div>
        </article>

        <article className="panel">
          <header>
            <h2>Execucao atual</h2>
            <p>Job em andamento e payload enviado.</p>
          </header>
          <JobDetails job={state.job_atual} />
        </article>

        <article className="panel">
          <header>
            <h2>Fila</h2>
            <p>Itens aguardando no worker.</p>
          </header>
          <QueueList items={state.fila} />
        </article>

        <article className="panel">
          <header>
            <h2>Historico</h2>
            <p>Ultimas execucoes.</p>
          </header>
          <HistoryList items={state.historico} />
        </article>
      </section>
    </main>
  );
}
