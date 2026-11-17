# Giunti Psychometrics — Digitalizador y Estructurador de Cuestionarios

Aplicación web full-stack para extraer, clasificar y estructurar automáticamente cuestionarios psicométricos y pruebas de evaluación desde documentos **PDF (`.pdf`)**, **Word (`.docx`)** y **Excel (`.xlsx`)** hacia un esquema JSON estandarizado.

---

## 🔗 Demo en Producción (Deploy)

- **Aplicación Web (Frontend — Vercel):** `[PENDIENTE_URL_FRONTEND]`
- **API & Documentación Interactiva Swagger (Backend — `/docs`):** `[PENDIENTE_URL_BACKEND]/docs`

---

## 🏗️ Arquitectura del Sistema

El Backend fue diseñado siguiendo **Arquitectura Hexagonal (Puertos y Adaptadores)** y procesamiento asíncrono mediante **Cola de Trabajos + Pool de Workers Concurrentes**:

```text
questionary_to_json/
├── examples/                  # Cuestionarios de prueba (.pdf, .docx, .xlsx) y sus .json resultantes
├── frontend/                  # Next.js (App Router, TypeScript, Tailwind CSS)
│   └── src/
│       ├── app/               # Interfaz principal de carga y seguimiento
│       ├── components/        # Inspector de ítems estructurados y visor JSON
│       ├── lib/api.ts         # Capa aislada de consumo HTTP hacia FastAPI
│       └── types/             # Contratos TypeScript alineados con Pydantic
└── backend/                   # Python 3.11+ · FastAPI · Pydantic v2
    ├── app/
    │   ├── domain/
    │   │   ├── schemas.py     # Modelos Pydantic (QuestionnaireOutput, QuestionItemSchema, ExtractionJob)
    │   │   ├── exceptions.py  # Jerarquía de excepciones de dominio (DomainError)
    │   │   └── ports.py       # Contratos (DocumentParserPort, LLMExtractorPort, JobQueuePort)
    │   ├── services/
    │   │   ├── parser_service.py     # Validación de formato/tamaño y enrutamiento por extensión
    │   │   └── extraction_worker.py  # Worker asíncrono consumidor de la cola
    │   ├── adapters/
    │   │   ├── parsers/       # PdfParser (pypdf), DocxParser (python-docx), XlsxParser (openpyxl)
    │   │   ├── llm/           # GeminiExtractorAdapter (Structured Outputs) y System Prompts
    │   │   └── queue/         # InMemoryJobQueue (asyncio.Queue concurrente)
    │   └── api/
    │       ├── dependencies.py # Inyección de dependencias con Annotated y @lru_cache
    │       └── routes.py       # Endpoints REST (/jobs, /jobs/{id}, /extract)
    └── tests/                 # Suite de 32 pruebas automatizadas con Pytest
```

### Flujo de Procesamiento
1. **Validación Temprana (`ParserService`):** Verifica que la extensión sea `.pdf`, `.docx` o `.xlsx`, que el archivo no esté vacío (`0 bytes`) y que no supere el tamaño máximo permitido (`MAX_FILE_SIZE_MB`).
2. **Encolado y Concurrencia (`InMemoryJobQueue` + `ExtractionWorker`):**
   - `POST /api/v1/questionnaires/jobs` permite subir uno o varios documentos simultáneamente, encolándolos con estado `QUEUED` (`202 Accepted`).
   - Un pool configurable de workers (`WORKER_CONCURRENCY`) consume la cola en segundo plano durante el `lifespan` de FastAPI, ejecutando la extracción documental en un hilo separado (`asyncio.to_thread`) y llamando al LLM de forma asíncrona sin bloquear el *event loop*.
   - Además, se expone `POST /api/v1/questionnaires/extract` para extracción síncrona directa de un documento individual (`200 OK`).
3. **Extracción Documental Especializada:**
   - **`.pdf` (`PdfParser`):** Extrae el texto página por página y detecta documentos corruptos o PDFs en blanco/escaneados sin capa de texto.
   - **`.docx` (`DocxParser`):** Extrae tanto los párrafos (`doc.paragraphs`) como las celdas de todas las tablas (`doc.tables`), indispensable para cuestionarios psicométricos donde las escalas Likert se maquetan en grillas tabulares.
   - **`.xlsx` (`XlsxParser`):** Recorre todas las hojas del libro (`openpyxl`), ignorando filas y celdas vacías y preservando la estructura tabular.
4. **Estructuración Garantizada con LLM (`GeminiExtractorAdapter`):**
   - Utiliza Google Gemini (`google-genai`) en su capa gratuita (*Free Tier*) con `response_schema` y `temperature=0.0`, seguido de validación estricta en Pydantic v2.

---

## 📋 Supuestos de Diseño e Interpretación Documentados

Siguiendo la indicación de la prueba técnica (*"Ante cualquier duda de interpretación, documenta tu supuesto en el README y avanza"*), se adoptaron los siguientes supuestos de diseño:

1. **Inferencia sin Etiquetas Explícitas:**
   - Se asume que los documentos reales **no** incluyen metadatos explícitos como `"Idioma: es"` ni `"Tipo: escala_likert"`. El motor infiere automáticamente el código ISO 639-1 del idioma (`it`, `es`, `en`, etc.), el título del instrumento y la clasificación de cada ítem a partir de la estructura semántica del enunciado y sus opciones.
2. **Representación de Ítems de `"emparejamiento"` (*Matching*):**
   - Para mantener 100% uniforme el contrato `alternativas: [{ "valor": ..., "texto": ... }]` en cuestionarios con o sin respuestas marcadas, cada premisa de la Columna A se lista con su identificador numérico (`"valor": "1"`, `"2"`, `"3"`) y cada opción asociable de la Columna B se lista con su identificador alfabético (`"valor": "A"`, `"B"`, `"C"`). Si el documento incluye la solución, se consigna en `"respuesta_correcta"` como cadena de pares (ej. `"1-B, 2-A, 3-C"`); en caso contrario, es `null`.
3. **Representación de Ítems de `"verdadero_falso"`:**
   - Se estructuran con sus dos alternativas en el idioma original del documento (ej. `[{"valor": "V", "texto": "Vero"}, {"valor": "F", "texto": "Falso"}]` en italiano; `Verdadero/Falso` en español; `T/F` `True/False` en inglés) y `"respuesta_correcta"` toma el valor `"V"`, `"F"`, `"T"` o `null` según esté o no indicada en el documento.
4. **Tipado de `"valor"` en `"escala_likert"` vs. otros tipos:**
   - En ítems de tipo `"escala_likert"`, el validador de dominio normaliza `"valor"` a entero (`int`: `0, 1, 2, 3...`) y fija `"respuesta_correcta": null`. En `"seleccion_multiple"`, `"verdadero_falso"` y `"emparejamiento"`, `"valor"` se mantiene como cadena (`str`: `"A"`, `"B"`, `"C"`). En `"desarrollo"`, el validador garantiza siempre `"alternativas": []` y `"respuesta_correcta": null`.
5. **Documentos sin Ítems Detectables (`NoItemsDetectedError`):**
   - Si el usuario sube un archivo `.pdf`, `.docx` o `.xlsx` válido que contiene texto pero ningún ítem de cuestionario (por ejemplo, una carta o factura), el sistema responde con código HTTP `422 Unprocessable Entity` (`code: "NO_ITEMS_DETECTED"`).

---

## ⚙️ Variables de Entorno

### Backend (`backend/.env`)
Puedes copiar la plantilla desde `backend/.env.example`:

| Variable | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | **(Requerido)** API Key gratuita de [Google AI Studio](https://aistudio.google.com/apikey) | — |
| `GEMINI_MODEL` | Modelo Gemini a utilizar | `gemini-3.5-flash-lite` |
| `APP_ENV` | Entorno de ejecución (`development` / `production`) | `development` |
| `MAX_FILE_SIZE_MB` | Tamaño máximo permitido por archivo en MB | `20` |
| `WORKER_CONCURRENCY` | Número de workers asíncronos procesando la cola en paralelo | `3` |

### Frontend (`frontend/.env.local`)
Puedes copiar la plantilla desde `frontend/.env.example`:

| Variable | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | URL base del Backend en FastAPI | `http://localhost:8000` |

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd questionary_to_json
```

### Opción Rápida — Con Docker Compose (Levanta Backend + Frontend en 1 comando)
```bash
cp backend/.env.example backend/.env
# Edita backend/.env y coloca tu GEMINI_API_KEY
docker compose up --build
```
- **Frontend:** `http://localhost:3000`
- **Backend API & Swagger:** `http://localhost:8000/docs`

---

### 2. Levantar el Backend Manualmente (FastAPI)

**Opción A — Usando `uv` (Recomendado):**
```bash
cd backend
cp .env.example .env
# Edita .env y coloca tu GEMINI_API_KEY
uv sync
uv run fastapi dev
```

**Opción B — Usando `venv` + `pip` estándar:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y coloca tu GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```
El Backend quedará disponible en `http://localhost:8000` (Swagger UI en `http://localhost:8000/docs`).

### 3. Levantar el Frontend (Next.js)
En otra terminal:
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```
Abre `http://localhost:3000` en tu navegador.

---

## 🧪 Ejecución de Tests Automatizados (Pytest)

La suite cuenta con **32 pruebas automatizadas** que validan el esquema de salida (`test_schemas.py`), los validadores y parsers de archivos `.pdf`, `.docx` y `.xlsx` incluyendo casos corruptos/vacíos (`test_validators_and_parsers.py`), el adaptador LLM con mocks (`test_llm_extractor.py`) y los endpoints HTTP síncronos y asíncronos (`test_api.py`):

```bash
cd backend
uv run pytest -v
```

---

## 📂 Archivos de Prueba (`/examples`)

En la carpeta [`/examples`](./examples) se incluyen **3 cuestionarios sintéticos de dominio público** (10 a 12 ítems cada uno, sin etiquetas artificiales de metadatos) junto con sus JSON estandarizados resultantes:

1. **`questionario_esempio_it.pdf` / `questionario_esempio_it.json`:** Cuestionario psicoactitudinal y cognitivo en **italiano (`it`)** de 10 ítems en 2 páginas.
2. **`cuestionario_psicometrico_es.docx` / `cuestionario_psicometrico_es.json`:** Inventario de competencias laborales en **español (`es`)** de 12 ítems (incluye tabla de escala Likert, selección múltiple, verdadero/falso, emparejamiento y desarrollo).
3. **`cognitive_assessment_en.xlsx` / `cognitive_assessment_en.json`:** Evaluación cognitiva y conductual en **inglés (`en`)** de 10 ítems en formato hoja de cálculo.
