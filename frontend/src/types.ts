export type JobType = "bluepex" | "consultor" | string;

export interface JobData {
  [key: string]: string | number | boolean | null | undefined;
}

export interface JobResult {
  sucesso?: boolean;
  mensagem?: string;
  ip?: string | null;
  [key: string]: string | number | boolean | null | undefined;
}

export interface JobItem {
  id: number;
  tipo: JobType;
  origem: string;
  status: string;
  sucesso: boolean | null;
  mensagem: string;
  dados: JobData;
  resultado: JobResult;
  inicio_iso?: string | null;
  inicio_humano?: string | null;
  fim_iso?: string | null;
  fim_humano?: string | null;
}

export interface StatusState {
  ocupado: boolean;
  job_atual: JobItem | null;
  fila: JobItem[];
  historico: JobItem[];
}

export interface SubmitResponse {
  ok: boolean;
  message: string;
  level?: "ok" | "aviso" | "erro";
  state?: StatusState;
  ticket?: {
    job_id: number;
    position: number;
  };
}

export interface Notice {
  id: number;
  text: string;
  level: "ok" | "aviso" | "erro";
}
