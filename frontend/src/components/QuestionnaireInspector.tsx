"use client";

import React, { useMemo, useState } from "react";
import {
  Check,
  CheckCircle2,
  Code2,
  Copy,
  Download,
  FileSpreadsheet,
  Globe,
  Hash,
  ListChecks,
} from "lucide-react";
import type {
  AlternativeItem,
  ItemType,
  QuestionItem,
  QuestionnaireOutput,
} from "@/types/questionnaire";

interface QuestionnaireInspectorProps {
  data: QuestionnaireOutput;
  sourceFilename: string;
}

const ITEM_TYPE_LABELS: Record<ItemType, string> = {
  escala_likert: "Escala Likert",
  seleccion_multiple: "Selección múltiple",
  verdadero_falso: "Verdadero / Falso",
  desarrollo: "Desarrollo",
  emparejamiento: "Emparejamiento",
};

const ITEM_TYPE_STYLES: Record<ItemType, string> = {
  escala_likert: "bg-[#eff6ff] text-[#1e3a8a] border-[#bfdbfe]",
  seleccion_multiple: "bg-[#f0fdf4] text-[#166534] border-[#bbf7d0]",
  verdadero_falso: "bg-[#fefce8] text-[#854d0e] border-[#fef08a]",
  desarrollo: "bg-[#f3f4f6] text-[#374151] border-[#d1d5db]",
  emparejamiento: "bg-[#f5f3ff] text-[#5b21b6] border-[#ddd6fe]",
};

const LANGUAGE_NAMES: Record<string, string> = {
  it: "Italiano (it)",
  es: "Español (es)",
  en: "Inglés (en)",
  pt: "Portugués (pt)",
  fr: "Francés (fr)",
};

function renderAlternatives(item: QuestionItem) {
  if (item.tipo === "desarrollo") {
    return (
      <div className="mt-3 rounded border border-dashed border-[#cbd5e1] bg-[#f8fafc] px-3.5 py-2.5 text-xs text-[#64748b]">
        Pregunta abierta de respuesta libre (sin alternativas predefinidas).
      </div>
    );
  }

  if (item.tipo === "escala_likert") {
    return (
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {item.alternativas.map((alt: AlternativeItem, idx: number) => (
          <div
            key={`${item.numero}-likert-${idx}`}
            className="flex items-center gap-2.5 rounded border border-[#dde2ea] bg-[#f8fafc] px-3 py-2 text-xs"
          >
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded bg-[#1e3a8a] px-1.5 font-[family-name:var(--font-mono)] text-[11px] font-semibold text-white tabular-nums">
              {String(alt.valor)}
            </span>
            <span className="font-medium text-[#1f2937]">{alt.texto}</span>
          </div>
        ))}
      </div>
    );
  }

  if (item.tipo === "emparejamiento") {
    const premises = item.alternativas.filter((a) => /^\d+$/.test(String(a.valor)));
    const options = item.alternativas.filter((a) => !/^\d+$/.test(String(a.valor)));

    if (premises.length > 0 && options.length > 0) {
      return (
        <div className="mt-3 space-y-2.5">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="rounded border border-[#dde2ea] bg-[#f8fafc] p-3">
              <p className="mb-2 text-[11px] font-semibold text-[#4b5563]">
                Columna A (Premisas)
              </p>
              <ul className="space-y-1.5 text-xs">
                {premises.map((p, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="rounded bg-[#e2e8f0] px-1.5 py-0.5 font-[family-name:var(--font-mono)] text-[11px] font-semibold text-[#1e293b]">
                      {String(p.valor)}
                    </span>
                    <span className="text-[#1f2937]">{p.texto}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded border border-[#dde2ea] bg-[#f8fafc] p-3">
              <p className="mb-2 text-[11px] font-semibold text-[#4b5563]">
                Columna B (Opciones asociables)
              </p>
              <ul className="space-y-1.5 text-xs">
                {options.map((o, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="rounded bg-[#ede9fe] px-1.5 py-0.5 font-[family-name:var(--font-mono)] text-[11px] font-semibold text-[#5b21b6]">
                      {String(o.valor)}
                    </span>
                    <span className="text-[#1f2937]">{o.texto}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          {item.respuesta_correcta !== null && (
            <div className="inline-flex items-center gap-1.5 rounded border border-[#a7f3d0] bg-[#ecfdf5] px-2.5 py-1 text-xs font-medium text-[#065f46]">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>
                Clave de asociación correcta:{" "}
                <strong className="font-[family-name:var(--font-mono)]">
                  {String(item.respuesta_correcta)}
                </strong>
              </span>
            </div>
          )}
        </div>
      );
    }
  }

  return (
    <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
      {item.alternativas.map((alt: AlternativeItem, idx: number) => {
        const isCorrect =
          item.respuesta_correcta !== null &&
          String(item.respuesta_correcta).trim().toLowerCase() ===
            String(alt.valor).trim().toLowerCase();

        return (
          <div
            key={`${item.numero}-alt-${idx}`}
            className={`flex items-center justify-between rounded border px-3 py-2 text-xs transition-colors ${
              isCorrect
                ? "border-[#6ee7b7] bg-[#ecfdf5] text-[#065f46]"
                : "border-[#dde2ea] bg-[#f8fafc] text-[#1f2937]"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span
                className={`inline-flex h-5 min-w-5 items-center justify-center rounded px-1.5 font-[family-name:var(--font-mono)] text-[11px] font-semibold ${
                  isCorrect
                    ? "bg-[#059669] text-white"
                    : "bg-[#e2e8f0] text-[#334155]"
                }`}
              >
                {String(alt.valor)}
              </span>
              <span className={isCorrect ? "font-semibold" : "font-normal"}>
                {alt.texto}
              </span>
            </div>
            {isCorrect && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#047857]">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Correcta
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function QuestionnaireInspector({
  data,
  sourceFilename,
}: QuestionnaireInspectorProps) {
  const [viewMode, setViewMode] = useState<"structured" | "json">("structured");
  const [selectedType, setSelectedType] = useState<ItemType | "ALL">("ALL");
  const [copied, setCopied] = useState(false);

  const formattedJson = useMemo(() => JSON.stringify(data, null, 2), [data]);

  const filteredItems = useMemo(() => {
    if (selectedType === "ALL") return data.items;
    return data.items.filter((i) => i.tipo === selectedType);
  }, [data.items, selectedType]);

  const typeCounts = useMemo(() => {
    const counts: Partial<Record<ItemType, number>> = {};
    for (const item of data.items) {
      counts[item.tipo] = (counts[item.tipo] || 0) + 1;
    }
    return counts;
  }, [data.items]);

  const handleCopyJson = async () => {
    await navigator.clipboard.writeText(formattedJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    const baseName = sourceFilename.replace(/\.[^/.]+$/, "") || "questionnaire";
    const blob = new Blob([formattedJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${baseName}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col rounded-md border border-[#dde2ea] bg-white">
      {/* Cabecera del Documento */}
      <div className="border-b border-[#dde2ea] px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1.5">
            <h2 className="text-lg font-semibold tracking-tight text-[#111827]">
              {data.titulo}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-[#4b5563]">
              <span className="inline-flex items-center gap-1.5 rounded border border-[#dde2ea] bg-[#f8fafc] px-2.5 py-0.5 font-medium text-[#1f2937]">
                <Globe className="h-3.5 w-3.5 text-[#1e3a8a]" />
                {LANGUAGE_NAMES[data.idioma] || `Idioma: ${data.idioma}`}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded border border-[#dde2ea] bg-[#f8fafc] px-2.5 py-0.5 font-medium text-[#1f2937] tabular-nums">
                <Hash className="h-3.5 w-3.5 text-[#1e3a8a]" />
                {data.total_items} {data.total_items === 1 ? "ítem" : "ítems"}
              </span>
              <span className="inline-flex items-center gap-1.5 text-[#6b7280]">
                <FileSpreadsheet className="h-3.5 w-3.5" />
                {sourceFilename}
              </span>
            </div>
          </div>

          {/* Controles de Vista y Exportación */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex rounded border border-[#dde2ea] bg-[#f1f5f9] p-0.5">
              <button
                type="button"
                onClick={() => setViewMode("structured")}
                className={`inline-flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-medium transition-colors ${
                  viewMode === "structured"
                    ? "bg-white text-[#111827] shadow-2xs"
                    : "text-[#4b5563] hover:text-[#111827]"
                }`}
              >
                <ListChecks className="h-3.5 w-3.5" />
                Ítems estructurados
              </button>
              <button
                type="button"
                onClick={() => setViewMode("json")}
                className={`inline-flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-medium transition-colors ${
                  viewMode === "json"
                    ? "bg-white text-[#111827] shadow-2xs"
                    : "text-[#4b5563] hover:text-[#111827]"
                }`}
              >
                <Code2 className="h-3.5 w-3.5" />
                JSON estandarizado
              </button>
            </div>

            <button
              type="button"
              onClick={handleCopyJson}
              className="inline-flex items-center gap-1.5 rounded border border-[#dde2ea] bg-white px-3 py-1.5 text-xs font-medium text-[#1f2937] transition-colors hover:bg-[#f8fafc]"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-[#059669]" />
                  Copiado
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5 text-[#4b5563]" />
                  Copiar JSON
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleDownloadJson}
              className="inline-flex items-center gap-1.5 rounded bg-[#1e3a8a] px-3.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#172554]"
            >
              <Download className="h-3.5 w-3.5" />
              Descargar .json
            </button>
          </div>
        </div>

        {/* Barra de Filtro por Tipo de Ítem */}
        {viewMode === "structured" && (
          <div className="mt-4 flex flex-wrap items-center gap-1.5 border-t border-[#eef1f5] pt-3.5">
            <button
              type="button"
              onClick={() => setSelectedType("ALL")}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors tabular-nums ${
                selectedType === "ALL"
                  ? "bg-[#1e3a8a] text-white"
                  : "bg-[#f1f5f9] text-[#4b5563] hover:bg-[#e2e8f0]"
              }`}
            >
              Todos ({data.items.length})
            </button>
            {(Object.keys(ITEM_TYPE_LABELS) as ItemType[]).map((type) => {
              const count = typeCounts[type] || 0;
              if (count === 0) return null;
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSelectedType(type)}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition-colors tabular-nums ${
                    selectedType === type
                      ? "bg-[#1e3a8a] text-white"
                      : "bg-[#f1f5f9] text-[#4b5563] hover:bg-[#e2e8f0]"
                  }`}
                >
                  {ITEM_TYPE_LABELS[type]} ({count})
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Cuerpo del Inspector */}
      {viewMode === "structured" ? (
        <div className="divide-y divide-[#eef1f5]">
          {filteredItems.map((item) => (
            <div key={item.numero} className="px-6 py-4 hover:bg-[#fafbfc]">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-baseline gap-2.5">
                  <span className="font-[family-name:var(--font-mono)] text-xs font-semibold text-[#1e3a8a] tabular-nums">
                    #{item.numero}
                  </span>
                  <p className="max-w-[72ch] text-sm font-medium leading-relaxed text-[#111827]">
                    {item.enunciado}
                  </p>
                </div>
                <span
                  className={`shrink-0 rounded border px-2 py-0.5 text-[11px] font-medium ${ITEM_TYPE_STYLES[item.tipo]}`}
                >
                  {ITEM_TYPE_LABELS[item.tipo]}
                </span>
              </div>

              {renderAlternatives(item)}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6">
          <pre className="max-h-[680px] overflow-auto rounded border border-[#1e293b] bg-[#0f172a] p-4 font-[family-name:var(--font-mono)] text-xs leading-relaxed text-[#e2e8f0]">
            <code>{formattedJson}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
