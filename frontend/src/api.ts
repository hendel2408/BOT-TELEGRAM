import type { StatusState, SubmitResponse } from "./types";


export async function fetchStatus(): Promise<StatusState> {
  const response = await fetch("/api/status", { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Falha ao carregar status.");
  }

  return (await response.json()) as StatusState;
}

async function postJson<T>(url: string, body: Record<string, string>): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  const payload = (await response.json()) as T;

  if (!response.ok) {
    throw new Error((payload as SubmitResponse).message || "Falha ao enviar requisicao.");
  }

  return payload;
}

export function submitBluepex(nome: string, mac: string): Promise<SubmitResponse> {
  return postJson<SubmitResponse>("/jobs/bluepex", { nome, mac });
}

export function submitConsultor(nome: string, data_limite: string): Promise<SubmitResponse> {
  return postJson<SubmitResponse>("/jobs/consultor", { nome, data_limite });
}
