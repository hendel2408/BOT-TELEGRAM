export const typeLabels = {
  bluepex: "BluePex",
  consultor: "Consultor"
};

export function resolveTypeLabel(type) {
  return typeLabels[type] || type || "Automacao";
}

export function resolveStatusTone(job) {
  if (!job) {
    return "idle";
  }

  if (job.status === "Executando") {
    return "running";
  }

  if (job.status === "Cancelado") {
    return "danger";
  }

  if (job.sucesso === true) {
    return "success";
  }

  if (job.sucesso === false) {
    return "danger";
  }

  return "idle";
}

export function summarizeJob(job) {
  if (!job) {
    return "Fila livre";
  }

  if (job.status === "Executando") {
    return `${resolveTypeLabel(job.tipo)} em andamento`;
  }

  if (job.status === "Cancelado") {
    return `${resolveTypeLabel(job.tipo)} cancelado`;
  }

  if (job.sucesso === true) {
    return `${resolveTypeLabel(job.tipo)} concluido`;
  }

  if (job.sucesso === false) {
    return `${resolveTypeLabel(job.tipo)} com falha`;
  }

  return resolveTypeLabel(job.tipo);
}
