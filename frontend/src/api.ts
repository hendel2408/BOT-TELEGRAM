import type { AuthState, StatusState, SubmitResponse } from "./types";


export async function fetchStatus(): Promise<StatusState> {
  const response = await fetch("/api/status", { cache: "no-store" });

  const payload = await parseJson(response);

  if (!response.ok) {
    throw new Error(extractMessage(payload, "Falha ao carregar status."));
  }

  return payload as unknown as StatusState;
}

async function postJson<T>(url: string, body: Record<string, string>): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  const payload = (await parseJson(response)) as T;

  if (!response.ok) {
    throw new Error(
      extractMessage(payload as Record<string, unknown>, "Falha ao enviar requisicao.")
    );
  }

  return payload;
}

async function parseJson(response: Response): Promise<Record<string, unknown>> {
  const raw = await response.text();

  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return {
      ok: false,
      message: "Resposta invalida do servidor."
    };
  }
}

function extractMessage(payload: Record<string, unknown>, fallback: string): string {
  const message = payload.message;
  return typeof message === "string" && message.trim() ? message : fallback;
}

export function submitBluepex(nome: string, mac: string): Promise<SubmitResponse> {
  return postJson<SubmitResponse>("/jobs/bluepex", { nome, mac });
}

export function submitConsultor(nome: string, data_limite: string): Promise<SubmitResponse> {
  return postJson<SubmitResponse>("/jobs/consultor", { nome, data_limite });
}

export function cancelJobs(): Promise<SubmitResponse> {
  return postJson<SubmitResponse>("/jobs/cancel", {});
}

export function loginPainel(login: string, senha: string): Promise<AuthState> {
  return postJson<AuthState>("/auth/login", { login, senha });
}

export function logoutPainel(): Promise<AuthState> {
  return postJson<AuthState>("/auth/logout", {});
}

export async function fetchAuthState(): Promise<AuthState> {
  const response = await fetch("/auth/me", { cache: "no-store" });
  const payload = await parseJson(response);

  if (!response.ok) {
    throw new Error(extractMessage(payload, "Falha ao consultar autenticacao."));
  }

  return payload as unknown as AuthState;
}
