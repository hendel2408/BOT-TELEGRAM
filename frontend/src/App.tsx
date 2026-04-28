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

type HistoryTypeFilter = "todos" | "bluepex" | "consultor";
type HistoryStatusFilter = "todos" | "concluido" | "falha";
type TimelineState = "done" | "active" | "pending" | "error";

interface TimelineStep {
  id: string;
  title: string;
  detail: string;
  at: string;
  state: TimelineState;
}

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

function statusLabel(status: string): string {
  if (status === "Concluido") {
    return "Concluido";
  }

  if (status === "Falha") {
    return "Falha";
  }

  return status || "-";
}

function HistoryList({ items }: { items: JobItem[] }) {
  if (!items.length) {
    return <p className="empty">Nenhum registro encontrado para o filtro atual.</p>;
  }

  return (
    <div className="list-grid">
      {items.map((item) => {
        const detalhe = item.resultado?.ip ? `IP ${item.resultado.ip}` : item.mensagem || "-";
        const statusClass =
          item.status === "Concluido"
            ? "success"
            : item.status === "Falha"
                ? "danger"
                : "idle";

        return (
          <article className="tile" key={item.id}>
            <header>
              <strong>{resolveTypeLabel(item.tipo)}</strong>
              <span>{item.fim_humano || item.inicio_humano || "-"}</span>
            </header>
            <p>
              <span className={`status-tag ${statusClass}`}>{statusLabel(item.status)}</span>
            </p>
            <p>Origem: {item.origem || "-"}</p>
            <p>Detalhe: {detalhe}</p>
          </article>
        );
      })}
    </div>
  );
}

function Timeline({ job, elapsed }: { job: JobItem | null; elapsed: string }) {
  const steps = buildTimeline(job);

  if (!job) {
    return <p className="empty">Sem execucao recente para montar timeline.</p>;
  }

  return (
    <div className="timeline-wrap">
      <div className="timeline-head">
        <strong>{resolveTypeLabel(job.tipo)}</strong>
        <span>Duracao: {elapsed}</span>
      </div>
      <ol className="timeline-list">
        {steps.map((step) => (
          <li className={`timeline-step ${step.state}`} key={step.id}>
            <span className="dot" />
            <div>
              <strong>{step.title}</strong>
              <p>{step.detail}</p>
              <small>{step.at}</small>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function buildTimeline(job: JobItem | null): TimelineStep[] {
  if (!job) {
    return [];
  }

  const startedAt = job.inicio_humano || "-";
  const endedAt = job.fim_humano || "-";

  const inQueue: TimelineStep = {
    id: "queue",
    title: "Enfileirado",
    detail: "Job recebido pelo backend.",
    at: startedAt,
    state: "done"
  };

  const running: TimelineStep = {
    id: "running",
    title: "Em execucao",
    detail: "Automacao rodando.",
    at: startedAt,
    state: "pending"
  };

  const completed: TimelineStep = {
    id: "final",
    title: "Finalizacao",
    detail: job.mensagem || "Processo finalizado.",
    at: endedAt,
    state: "pending"
  };

  if (job.status === "Executando") {
    running.state = "active";
    return [inQueue, running, completed];
  }

  if (job.status === "Concluido") {
    running.state = "done";
    completed.state = "done";
    completed.title = "Concluido";
    return [inQueue, running, completed];
  }

  if (job.status === "Falha") {
    running.state = "done";
    completed.state = "error";
    completed.title = "Falha";
    return [inQueue, running, completed];
  }

  inQueue.state = "active";
  running.state = "pending";
  return [inQueue, running, completed];
}

function elapsedFromJob(job: JobItem | null, nowMs: number): string {
  if (!job || !job.inicio_iso) {
    return "-";
  }

  const startMs = Date.parse(job.inicio_iso);
  if (Number.isNaN(startMs)) {
    return "-";
  }

  const endMs = job.fim_iso ? Date.parse(job.fim_iso) : nowMs;
  const diff = Math.max(0, Math.floor((endMs - startMs) / 1000));

  const hours = Math.floor(diff / 3600);
  const minutes = Math.floor((diff % 3600) / 60);
  const seconds = diff % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }

  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }

  return `${seconds}s`;
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
  const [clockMs, setClockMs] = useState(Date.now());
  const [bluepexNome, setBluepexNome] = useState("");
  const [bluepexMac, setBluepexMac] = useState("");
  const [consultorNome, setConsultorNome] = useState("");
  const [consultorData, setConsultorData] = useState("");
  const [login, setLogin] = useState("");
  const [senha, setSenha] = useState("");
  const [historyTypeFilter, setHistoryTypeFilter] = useState<HistoryTypeFilter>("todos");
  const [historyStatusFilter, setHistoryStatusFilter] = useState<HistoryStatusFilter>("todos");
  const [historyQuery, setHistoryQuery] = useState("");

  const statusLabelText = useMemo(() => summarizeJob(state.job_atual), [state.job_atual]);
  const statusTone = useMemo(() => resolveStatusTone(state.job_atual), [state.job_atual]);

  const timelineJob = state.job_atual ?? state.historico[0] ?? null;
  const timelineElapsed = elapsedFromJob(timelineJob, clockMs);

  const filteredHistory = useMemo(() => {
    const query = historyQuery.trim().toLowerCase();

    return state.historico.filter((item) => {
      const typeOk = historyTypeFilter === "todos" || item.tipo === historyTypeFilter;

      const statusOk =
        historyStatusFilter === "todos" ||
        (historyStatusFilter === "concluido" && item.status === "Concluido") ||
        (historyStatusFilter === "falha" && item.status === "Falha");

      if (!typeOk || !statusOk) {
        return false;
      }

      if (!query) {
        return true;
      }

      const haystack = `${item.tipo} ${item.origem} ${item.mensagem} ${JSON.stringify(item.dados)} ${JSON.stringify(item.resultado)}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [state.historico, historyQuery, historyStatusFilter, historyTypeFilter]);

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

    const timer = window.setInterval(() => {
      setClockMs(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [isAuthenticated]);

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
          <span className={`status-pill ${statusTone}`}>{statusLabelText}</span>
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
            <h2>Linha do tempo</h2>
            <p>Acompanhamento em tempo real da execucao atual.</p>
          </header>
          <Timeline job={timelineJob} elapsed={timelineElapsed} />
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

        <article className="panel panel-wide">
          <header>
            <h2>Historico</h2>
            <p>Filtros por tipo, status e busca textual.</p>
          </header>
          <div className="history-filters">
            <label>
              <span>Tipo</span>
              <select
                value={historyTypeFilter}
                onChange={(event) => setHistoryTypeFilter(event.target.value as HistoryTypeFilter)}
              >
                <option value="todos">Todos</option>
                <option value="bluepex">BluePex</option>
                <option value="consultor">Consultor</option>
              </select>
            </label>
            <label>
              <span>Status</span>
              <select
                value={historyStatusFilter}
                onChange={(event) => setHistoryStatusFilter(event.target.value as HistoryStatusFilter)}
              >
                <option value="todos">Todos</option>
                <option value="concluido">Concluido</option>
                <option value="falha">Falha</option>
              </select>
            </label>
            <label>
              <span>Busca</span>
              <input
                value={historyQuery}
                onChange={(event) => setHistoryQuery(event.target.value)}
                placeholder="Nome, MAC, IP, mensagem..."
              />
            </label>
          </div>
          <HistoryList items={filteredHistory} />
        </article>
      </section>
    </main>
  );
}
