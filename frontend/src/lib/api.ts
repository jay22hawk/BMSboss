/**
 * BMS Boss — API Client
 * Communicates with the FastAPI extraction service.
 */

import type {
  ExtractionResponse,
  GenerationResponse,
  ExtractAndMergeResponse,
  BMSCalculatorInput,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Upload a PDF bill and extract structured data.
 */
export async function extractBill(
  file: File,
): Promise<ExtractionResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/extract`, {
    method: "POST",
    body: form,
  });
  return handleResponse<ExtractionResponse>(res);
}

/**
 * Upload a PDF, extract, and return pre-populated calculator input.
 */
export async function extractAndMerge(
  file: File,
): Promise<ExtractAndMergeResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/extract-and-merge`, {
    method: "POST",
    body: form,
  });
  return handleResponse<ExtractAndMergeResponse>(res);
}

/**
 * Generate an Excel file from calculator input data.
 */
export async function generateExcel(
  input: BMSCalculatorInput,
): Promise<GenerationResponse> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return handleResponse<GenerationResponse>(res);
}

/**
 * Download a generated Excel file.
 */
export function getDownloadUrl(fileId: string): string {
  return `${API_BASE}/download/${fileId}`;
}

/**
 * Health check.
 */
export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse(res);
}
