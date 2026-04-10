import { FormEvent, useEffect, useMemo, useState } from "react";

import { fetchStatus, submitBluepex, submitConsultor } from "./api";
import type { JobItem, Notice, StatusState } from "./types";
import { resolveStatusTone, resolveTypeLabel, summarizeJob } from "./utils/labels.js";


function Field(props: {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  const { label, name, value, onChange, placeholder } = props;

  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function SectionHeader(props: { title: string; subtitle: string; extra?: string }) {
  return (
    <div className="panel-header">
      <div>
        <h2>{props.title}</h2>
        <p>{props.subtitle}</p>
      </div>
      {props.extra ? <span className="secondary-chip">{props.extra}</span> : null}
    </div>
  );
}

function JobDetails({ job }: { job: JobItem | null }) {
  if (!job) {
    return <p className="empty">Nenhuma automacao em execucao.</p>;
  }

  const entries = [
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
        <div className="detail-item" key={label}>
          <strong>{label}</strong>
          <div className="meta">{value}</div>
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
    <div className="queue-list">
      {items.map((item, index) => (
        <div className="queue-item" key={item.id}>
          <div>
            <strong>{resolveTypeLabel(item.tipo)}</strong>
            <div className="meta">
              Origem: {item.origem || "-"}
              <br />
              Dados: {JSON.stringify(item.dados || {})}
            </div>
          </div>
          <span className="secondary-chip">Posicao {index + 1}</span>
        </div>
      ))}
    </div>
  );
}

function HistoryList({ items }: { items: JobItem[] }) {
  if (!items.length) {
    return <p className="empty">Nenhuma execucao registrada.</p>;
  }

  return (
    <div className="history-list">
      {items.map((item) => {
        const detalhe = item.resultado?.ip ? `IP ${item.resultado.ip}` : item.mensagem || "-";

        return (
          <div className="history-item" key={item.id}>
            <div className="history-item-header">
              <strong>{resolveTypeLabel(item.tipo)}</strong>
              <span>{item.fim_humano || item.inicio_humano || "-"}</span>
            </div>
            <div className="meta">
              Status: {item.status}
              <br />
              Origem: {item.origem || "-"}
              <br />
              Mensagem: {item.mensagem || "-"}
              <br />
              Detalhe: {detalhe}
            </div>
          </div>
        );
      })}
    </div>
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

const EMPTY_STATE: StatusState = {
  ocupado: false,
  job_atual: null,
  fila: [],
  historico: []
};

export function App() {
  const [state, setState] = useState<StatusState>(EMPTY_STATE);
  const [isLoading, setIsLoading] = useState(true);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [isSendingBluepex, setIsSendingBluepex] = useState(false);
  const [isSendingConsultor, setIsSendingConsultor] = useState(false);
  const [bluepexNome, setBluepexNome] = useState("");
  const [bluepexMac, setBluepexMac] = useState("");
  const [consultorNome, setConsultorNome] = useState("");
  const [consultorData, setConsultorData] = useState("");

  useEffect(() => {
    let active = true;

    async function loadInitialStatus() {
      try {
        const payload = await fetchStatus();
        if (active) {
          setState(payload);
        }
      } catch (error) {
        if (active) {
          pushNotice(error instanceof Error ? error.message : "Falha ao carregar status.", "erro");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    loadInitialStatus();

    const timer = window.setInterval(async () => {
      try {
        const payload = await fetchStatus();
        if (active) {
          setState(payload);
        }
      } catch (error) {
        console.error(error);
      }
    }, 2000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const statusLabel = useMemo(() => summarizeJob(state.job_atual), [state.job_atual]);
  const statusTone = useMemo(() => resolveStatusTone(state.job_atual), [state.job_atual]);

  function pushNotice(text: string, level: Notice["level"]) {
    const notice: Notice = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      text,
      level
    };

    setNotices((current) => [notice, ...current].slice(0, 3));
    window.setTimeout(() => {
      setNotices((current) => current.filter((item) => item.id !== notice.id));
    }, 5000);
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

  if (isLoading) {
    return <div className="loading-state">Carregando painel...</div>;
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Frontend isolado</p>
        <h1>Painel desacoplado do backend.</h1>
        <p>
          Esta interface roda sozinha em React com TypeScript e conversa com o Flask apenas por API.
          O backend pode continuar estavel enquanto o frontend evolui em outra mao.
        </p>
        <div className="hero-bar">
          <span className={`status-pill ${statusTone}`}>{statusLabel}</span>
          <span className="secondary-chip">Fila: {state.fila.length}</span>
          <span className="secondary-chip">Historico: {state.historico.length}</span>
        </div>
      </section>

      <div className="layout">
        <div className="stack">
          <section className="panel">
            <SectionHeader title="Nova execucao" subtitle="Forms diretos consumindo a API do backend." />
            <div className="panel-body">
              <NoticeStack notices={notices} />
              <div className="grid-two">
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
                  <div className="button-row">
                    <button className="primary-button" disabled={isSendingBluepex} type="submit">
                      {isSendingBluepex ? "Enviando..." : "Executar BluePex"}
                    </button>
                  </div>
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
                  <div className="button-row">
                    <button className="primary-button" disabled={isSendingConsultor} type="submit">
                      {isSendingConsultor ? "Enviando..." : "Executar Consultor"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </section>

          <section className="panel">
            <SectionHeader title="Execucao atual" subtitle="Leitura do job em andamento e dos dados enviados." extra={statusLabel} />
            <div className="panel-body">
              <JobDetails job={state.job_atual} />
            </div>
          </section>
        </div>

        <div className="stack">
          <section className="panel">
            <SectionHeader title="Fila" subtitle="Itens aguardando no worker." extra={`${state.fila.length} pendente(s)`} />
            <div className="panel-body">
              <QueueList items={state.fila} />
            </div>
          </section>

          <section className="panel">
            <SectionHeader title="Historico" subtitle="Ultimas automacoes concluídas ou com falha." />
            <div className="panel-body">
              <HistoryList items={state.historico} />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
