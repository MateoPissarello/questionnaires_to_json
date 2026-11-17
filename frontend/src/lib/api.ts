import type {
  BackendErrorPayload,
  ExtractionJob,
  QuestionnaireOutput,
} from "@/types/questionnaire";

/**
 * ============================================================================
 * CAPA DE CONSUMO DE API DEL BACKEND (FastAPI)
 * ============================================================================
 * Si necesitas cambiar la URL del servidor, los rutas de los endpoints o los
 * headers HTTP (ej. agregar un token de autorización), este es el ÚNICO archivo
 * que debes modificar.
 *
 * Variable de entorno:
 *   NEXT_PUBLIC_API_URL (por defecto apunta a "http://localhost:8000")
 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : typeof window !== "undefined" && window.location.port === "3000"
      ? "http://localhost:8000"
      : ""
).replace(/\/+$/, "");

const QUESTIONNAIRES_PREFIX = `${API_BASE_URL}/api/v1/questionnaires`;

/**
 * Error tipado que conserva el código de dominio (`UNSUPPORTED_FILE_FORMAT`,
 * `NO_ITEMS_DETECTED`, `EMPTY_DOCUMENT`, etc.) y el HTTP status devueltos por FastAPI.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;

  constructor(message: string, status: number, code = "API_ERROR") {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

/**
 * Helper interno para parsear errores HTTP devueltos por FastAPI (`main.py`).
 */
async function parseErrorResponse(response: Response): Promise<ApiClientError> {
  try {
    const payload = (await response.json()) as BackendErrorPayload;
    const message =
      typeof payload.detail === "string"
        ? payload.detail
        : `Error HTTP ${response.status} al comunicarse con el servidor.`;
    const code = payload.code || `HTTP_${response.status}`;
    return new ApiClientError(message, response.status, code);
  } catch {
    return new ApiClientError(
      `Error HTTP ${response.status}: ${response.statusText || "Respuesta inválida del servidor"}`,
      response.status
    );
  }
}

/**
 * 1. HEALTH CHECK (`GET /health`)
 * Verifica si el Backend FastAPI está en línea.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (!response.ok) return false;
    const data = (await response.json()) as { status?: string };
    return data.status === "ok";
  } catch {
    return false;
  }
}

/**
 * 2. ENCOLADO ASÍNCRONO MULTI-ARCHIVO (`POST /api/v1/questionnaires/jobs`)
 * Envía 1 o varios archivos (.pdf, .docx, .xlsx) en un `FormData` bajo la llave `"files"`.
 * Recibe inmediatamente `202 Accepted` con la lista de `ExtractionJob` en estado `"QUEUED"`.
 */
export async function enqueueQuestionnaireFiles(
  files: File[]
): Promise<ExtractionJob[]> {
  const formData = new FormData();
  for (const file of files) {
    // El nombre del campo "files" coincide con `files: list[UploadFile]` en routes.py
    formData.append("files", file);
  }

  const response = await fetch(`${QUESTIONNAIRES_PREFIX}/jobs`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return (await response.json()) as ExtractionJob[];
}

/**
 * 3. CONSULTA DE ESTADO DE UN JOB (`GET /api/v1/questionnaires/jobs/{job_id}`)
 * Se invoca periódicamente (polling) mientras el job esté en `"QUEUED"` o `"PROCESSING"`.
 * Cuando pasa a `"COMPLETED"`, `job.result` trae el `QuestionnaireOutput` completo.
 */
export async function getExtractionJobById(
  jobId: string
): Promise<ExtractionJob> {
  const response = await fetch(
    `${QUESTIONNAIRES_PREFIX}/jobs/${encodeURIComponent(jobId)}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return (await response.json()) as ExtractionJob;
}

/**
 * 4. EXTRACCIÓN SÍNCRONA DIRECTA (`POST /api/v1/questionnaires/extract`)
 * Envía un único archivo bajo la llave `"file"` y espera a que el servidor
 * retorne directamente el `QuestionnaireOutput` (`200 OK`).
 */
export async function extractSingleQuestionnaireSync(
  file: File
): Promise<QuestionnaireOutput> {
  const formData = new FormData();
  // El nombre del campo "file" coincide con `file: UploadFile` en routes.py
  formData.append("file", file);

  const response = await fetch(`${QUESTIONNAIRES_PREFIX}/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return (await response.json()) as QuestionnaireOutput;
}
