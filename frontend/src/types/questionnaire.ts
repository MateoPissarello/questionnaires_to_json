/**
 * Tipos de ítem soportados por el dominio del Backend (`app/domain/schemas.py`).
 */
export type ItemType =
  | "escala_likert"
  | "seleccion_multiple"
  | "verdadero_falso"
  | "desarrollo"
  | "emparejamiento";

/**
 * Estados del ciclo de vida de un trabajo en la cola asíncrona.
 */
export type JobStatus = "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";

/**
 * Alternativa de respuesta individual (`AlternativeSchema`).
 */
export interface AlternativeItem {
  valor: number | string;
  texto: string;
}

/**
 * Ítem individual del cuestionario (`QuestionItemSchema`).
 */
export interface QuestionItem {
  numero: number;
  enunciado: string;
  tipo: ItemType;
  alternativas: AlternativeItem[];
  respuesta_correcta: number | string | null;
}

/**
 * Esquema estandarizado de salida del cuestionario (`QuestionnaireOutput`).
 */
export interface QuestionnaireOutput {
  titulo: string;
  idioma: string;
  total_items: number;
  items: QuestionItem[];
}

/**
 * Respuesta de un trabajo en la cola asíncrona (`ExtractionJob`).
 */
export interface ExtractionJob {
  job_id: string;
  filename: string;
  status: JobStatus;
  created_at: string;
  completed_at: string | null;
  result: QuestionnaireOutput | null;
  error: string | null;
}

/**
 * Estructura de error semántico devuelta por el exception_handler de FastAPI.
 */
export interface BackendErrorPayload {
  detail?: string;
  code?: string;
}
