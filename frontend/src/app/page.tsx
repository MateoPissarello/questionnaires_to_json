"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  FolderUp,
  Loader2,
  Trash2,
  Upload,
} from "lucide-react";
import {
  ApiClientError,
  enqueueQuestionnaireFiles,
  getExtractionJobById,
} from "@/lib/api";
import type { ExtractionJob } from "@/types/questionnaire";
import { QuestionnaireInspector } from "@/components/QuestionnaireInspector";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".xlsx"];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(2)} MB`;
}

export default function WorkbenchPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [jobs, setJobs] = useState<ExtractionJob[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const hasPendingJobs = jobs.some(
    (j) => j.status === "QUEUED" || j.status === "PROCESSING"
  );

  useEffect(() => {
    if (!hasPendingJobs) return;

    const interval = setInterval(async () => {
      const pendingIds = jobs
        .filter((j) => j.status === "QUEUED" || j.status === "PROCESSING")
        .map((j) => j.job_id);

      if (pendingIds.length === 0) return;

      const updatedResults = await Promise.all(
        pendingIds.map(async (id) => {
          try {
            return await getExtractionJobById(id);
          } catch {
            return null;
          }
        })
      );

      const updatesById = new Map<string, ExtractionJob>();
      for (const item of updatedResults) {
        if (item) updatesById.set(item.job_id, item);
      }

      if (updatesById.size > 0) {
        setJobs((prev) =>
          prev.map((job) => updatesById.get(job.job_id) ?? job)
        );
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [hasPendingJobs, jobs]);

  const handleAddFiles = useCallback((fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setErrorMessage(null);

    const incoming = Array.from(fileList);
    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map((f) => `${f.name}-${f.size}`));
      const deduplicated = incoming.filter(
        (f) => !existingNames.has(`${f.name}-${f.size}`)
      );
      return [...prev, ...deduplicated];
    });
  }, []);

  const handleRemoveStagedFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleProcessFiles = async () => {
    if (selectedFiles.length === 0 || isSubmitting) return;
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const createdJobs = await enqueueQuestionnaireFiles(selectedFiles);
      setJobs((prev) => [...createdJobs, ...prev]);
      if (createdJobs.length > 0) {
        setActiveJobId(createdJobs[0].job_id);
      }
      setSelectedFiles([]);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(
          "No fue posible procesar el documento en este momento. Inténtalo nuevamente."
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeJob = jobs.find((j) => j.job_id === activeJobId) ?? jobs[0] ?? null;

  return (
    <div className="flex min-h-screen flex-col bg-[#f6f7f9]">
      {/* Barra Superior */}
      <header className="border-b border-[#dde2ea] bg-white">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-[#1e3a8a] text-xs font-bold tracking-tight text-white">
              GP
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight text-[#111827]">
                Giunti Psychometrics · Digitalizador de Cuestionarios
              </h1>
              <p className="text-[11px] text-[#6b7280]">
                Convierte cuestionarios en PDF, Word o Excel a formato JSON estandarizado
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Contenedor Principal */}
      <main className="mx-auto grid w-full max-w-[1440px] flex-1 grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[360px_1fr]">
        {/* Columna Izquierda: Carga de Archivos e Historial de Documentos */}
        <aside className="flex flex-col gap-5">
          {/* Panel de Subida */}
          <section className="rounded-md border border-[#dde2ea] bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-[#111827]">
                Subir cuestionario
              </h2>
              <span className="font-[family-name:var(--font-mono)] text-[11px] text-[#6b7280]">
                {ALLOWED_EXTENSIONS.join(" · ")}
              </span>
            </div>

            {/* Dropzone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                handleAddFiles(e.dataTransfer.files);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`cursor-pointer rounded border border-dashed px-4 py-6 text-center transition-colors ${
                isDragging
                  ? "border-[#1e3a8a] bg-[#eff6ff]"
                  : "border-[#cbd5e1] bg-[#f8fafc] hover:border-[#94a3b8] hover:bg-[#f1f5f9]"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.xlsx"
                onChange={(e) => {
                  handleAddFiles(e.target.files);
                  e.target.value = "";
                }}
                className="hidden"
              />
              <FolderUp className="mx-auto h-6 w-6 text-[#1e3a8a]" />
              <p className="mt-2 text-xs font-medium text-[#1f2937]">
                Arrastra tu documento aquí o haz clic para seleccionarlo
              </p>
              <p className="mt-1 text-[11px] text-[#6b7280]">
                Formatos admitidos: PDF, Word (.docx) y Excel (.xlsx)
              </p>
            </div>

            {/* Lista de archivos seleccionados */}
            {selectedFiles.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
                  {selectedFiles.map((file, idx) => (
                    <div
                      key={`${file.name}-${idx}`}
                      className="flex items-center justify-between rounded border border-[#dde2ea] bg-[#f8fafc] px-2.5 py-1.5 text-xs"
                    >
                      <div className="flex min-w-0 items-center gap-2">
                        <FileText className="h-3.5 w-3.5 shrink-0 text-[#1e3a8a]" />
                        <span className="truncate font-medium text-[#1f2937]">
                          {file.name}
                        </span>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <span className="text-[11px] text-[#6b7280] tabular-nums">
                          {formatBytes(file.size)}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveStagedFile(idx);
                          }}
                          className="rounded p-0.5 text-[#6b7280] hover:bg-[#e2e8f0] hover:text-[#991b1b]"
                          aria-label={`Quitar ${file.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={handleProcessFiles}
                  className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded bg-[#1e3a8a] px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-[#172554] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Iniciando conversión...
                    </>
                  ) : (
                    <>
                      <Upload className="h-3.5 w-3.5" />
                      {selectedFiles.length === 1
                        ? "Convertir a JSON"
                        : `Convertir ${selectedFiles.length} documentos a JSON`}
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Mensaje de Error */}
            {errorMessage && (
              <div className="mt-3 rounded border border-[#fecaca] bg-[#fef2f2] p-3 text-xs text-[#991b1b]">
                <div className="flex items-start gap-2">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#dc2626]" />
                  <p className="leading-relaxed">{errorMessage}</p>
                </div>
              </div>
            )}
          </section>

          {/* Panel de Documentos Procesados */}
          <section className="flex flex-1 flex-col rounded-md border border-[#dde2ea] bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-[#111827]">
                Documentos recientes
              </h2>
              <span className="rounded bg-[#eef1f5] px-2 py-0.5 font-[family-name:var(--font-mono)] text-[11px] font-medium text-[#4b5563] tabular-nums">
                {jobs.length}
              </span>
            </div>

            {jobs.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center rounded border border-dashed border-[#e2e8f0] bg-[#fafbfc] px-4 py-8 text-center">
                <Clock className="h-5 w-5 text-[#94a3b8]" />
                <p className="mt-2 text-xs font-medium text-[#4b5563]">
                  Aún no hay cuestionarios cargados
                </p>
                <p className="mt-1 text-[11px] text-[#6b7280]">
                  Sube un archivo arriba para ver sus preguntas y descargar el JSON.
                </p>
              </div>
            ) : (
              <div className="space-y-2 overflow-y-auto">
                {jobs.map((job) => {
                  const isSelected = activeJob?.job_id === job.job_id;
                  return (
                    <button
                      key={job.job_id}
                      type="button"
                      onClick={() => setActiveJobId(job.job_id)}
                      className={`w-full rounded border p-3 text-left transition-colors ${
                        isSelected
                          ? "border-[#1e3a8a] bg-[#eff6ff]"
                          : "border-[#dde2ea] bg-white hover:bg-[#f8fafc]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="truncate text-xs font-semibold text-[#111827]">
                          {job.filename}
                        </span>
                        {job.status === "COMPLETED" && (
                          <span className="inline-flex shrink-0 items-center gap-1 rounded border border-[#a7f3d0] bg-[#ecfdf5] px-1.5 py-0.5 text-[10px] font-semibold text-[#065f46]">
                            <CheckCircle2 className="h-3 w-3" />
                            Completado
                          </span>
                        )}
                        {(job.status === "QUEUED" ||
                          job.status === "PROCESSING") && (
                          <span className="inline-flex shrink-0 items-center gap-1 rounded border border-[#fde68a] bg-[#fffbeb] px-1.5 py-0.5 text-[10px] font-semibold text-[#92400e]">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Analizando
                          </span>
                        )}
                        {job.status === "FAILED" && (
                          <span className="inline-flex shrink-0 items-center gap-1 rounded border border-[#fecaca] bg-[#fef2f2] px-1.5 py-0.5 text-[10px] font-semibold text-[#991b1b]">
                            <AlertCircle className="h-3 w-3" />
                            Error
                          </span>
                        )}
                      </div>

                      {job.result && (
                        <div className="mt-1.5 flex items-center gap-2 text-[11px] text-[#4b5563]">
                          <span className="truncate">{job.result.titulo}</span>
                          <span>·</span>
                          <span className="shrink-0 font-medium tabular-nums">
                            {job.result.total_items} ítems ({job.result.idioma})
                          </span>
                        </div>
                      )}

                      {job.error && (
                        <p className="mt-1.5 line-clamp-2 text-[11px] text-[#991b1b]">
                          {job.error}
                        </p>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        </aside>

        {/* Columna Derecha: Resultado y Descarga */}
        <section className="flex flex-col">
          {!activeJob ? (
            <div className="flex flex-1 flex-col items-center justify-center rounded-md border border-[#dde2ea] bg-white p-10 text-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-md border border-[#dde2ea] bg-[#f8fafc] text-[#1e3a8a]">
                <FileText className="h-5 w-5" />
              </div>
              <h2 className="mt-4 text-base font-semibold text-[#111827]">
                Convierte tus cuestionarios a JSON en segundos
              </h2>
              <p className="mt-1.5 max-w-[52ch] text-xs leading-relaxed text-[#4b5563]">
                Adjunta un archivo PDF, Word (.docx) o Excel (.xlsx) en el panel izquierdo para extraer automáticamente sus preguntas, alternativas de respuesta y clave de corrección.
              </p>

              <div className="mt-6 grid w-full max-w-xl grid-cols-1 gap-3 text-left sm:grid-cols-3">
                <div className="rounded border border-[#dde2ea] bg-[#f8fafc] p-3">
                  <p className="text-xs font-semibold text-[#111827]">
                    1. Sube tu archivo
                  </p>
                  <p className="mt-1 text-[11px] leading-relaxed text-[#4b5563]">
                    Acepta pruebas y cuestionarios en formato PDF, Word o Excel.
                  </p>
                </div>
                <div className="rounded border border-[#dde2ea] bg-[#f8fafc] p-3">
                  <p className="text-xs font-semibold text-[#111827]">
                    2. Revisa los ítems
                  </p>
                  <p className="mt-1 text-[11px] leading-relaxed text-[#4b5563]">
                    Visualiza el título, idioma, tipo de pregunta y sus alternativas.
                  </p>
                </div>
                <div className="rounded border border-[#dde2ea] bg-[#f8fafc] p-3">
                  <p className="text-xs font-semibold text-[#111827]">
                    3. Descarga el JSON
                  </p>
                  <p className="mt-1 text-[11px] leading-relaxed text-[#4b5563]">
                    Copia o descarga el resultado listo para cargar en la plataforma.
                  </p>
                </div>
              </div>
            </div>
          ) : activeJob.status === "QUEUED" ||
            activeJob.status === "PROCESSING" ? (
            <div className="flex flex-1 flex-col rounded-md border border-[#dde2ea] bg-white p-6">
              <div className="flex items-center gap-3 border-b border-[#eef1f5] pb-4">
                <Loader2 className="h-5 w-5 animate-spin text-[#1e3a8a]" />
                <div>
                  <h2 className="text-sm font-semibold text-[#111827]">
                    Estructurando {activeJob.filename}...
                  </h2>
                  <p className="text-xs text-[#6b7280]">
                    Identificando preguntas, alternativas de respuesta e idioma del documento...
                  </p>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                {[1, 2, 3, 4].map((n) => (
                  <div
                    key={n}
                    className="animate-pulse rounded border border-[#eef1f5] p-4"
                  >
                    <div className="h-4 w-3/4 rounded bg-[#e2e8f0]" />
                    <div className="mt-3 grid grid-cols-4 gap-2">
                      <div className="h-7 rounded bg-[#f1f5f9]" />
                      <div className="h-7 rounded bg-[#f1f5f9]" />
                      <div className="h-7 rounded bg-[#f1f5f9]" />
                      <div className="h-7 rounded bg-[#f1f5f9]" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : activeJob.status === "FAILED" ? (
            <div className="flex flex-1 flex-col items-center justify-center rounded-md border border-[#fecaca] bg-white p-10 text-center">
              <AlertCircle className="h-8 w-8 text-[#dc2626]" />
              <h2 className="mt-3 text-base font-semibold text-[#111827]">
                No se pudo procesar {activeJob.filename}
              </h2>
              <p className="mt-1.5 max-w-[50ch] text-xs leading-relaxed text-[#991b1b]">
                {activeJob.error ||
                  "El documento no contiene preguntas detectables o su formato no es válido."}
              </p>
            </div>
          ) : activeJob.result ? (
            <QuestionnaireInspector
              data={activeJob.result}
              sourceFilename={activeJob.filename}
            />
          ) : null}
        </section>
      </main>
    </div>
  );
}
