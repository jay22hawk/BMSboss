"use client";

import { useState, useCallback } from "react";
import type { ExtractedBillData, BMSCalculatorInput } from "@/types";
import { extractAndMerge } from "@/lib/api";

interface UploadStepProps {
  onComplete: (
    data: ExtractedBillData,
    merged: BMSCalculatorInput | null,
    warnings: string[],
  ) => void;
}

export function UploadStep({ onComplete }: UploadStepProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile?.type === "application/pdf") {
      setFile(droppedFile);
      setError(null);
    } else {
      setError("Please upload a PDF file.");
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) {
        if (selected.type === "application/pdf") {
          setFile(selected);
          setError(null);
        } else {
          setError("Please upload a PDF file.");
        }
      }
    },
    [],
  );

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const result = await extractAndMerge(file);

      if (result.success && result.extraction.data) {
        onComplete(
          result.extraction.data,
          result.calculator_input,
          result.extraction.warnings,
        );
      } else {
        const errors = result.extraction.errors;
        setError(
          errors.length > 0
            ? errors.join("; ")
            : "Extraction failed. Please try a different file.",
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect to extraction service.",
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Upload Utility Bill
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Upload a PDF of the utility energy bill. BMS Boss will automatically
        detect the sponsor and extract billing data.
      </p>

      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
          dragActive
            ? "border-brand-500 bg-blue-50"
            : file
              ? "border-green-400 bg-green-50"
              : "border-gray-300 hover:border-gray-400"
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileSelect}
        />

        {file ? (
          <div>
            <svg
              className="w-12 h-12 mx-auto text-green-500 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="font-medium text-gray-900">{file.name}</p>
            <p className="text-sm text-gray-500 mt-1">
              {(file.size / 1024).toFixed(1)} KB &mdash; Click to change
            </p>
          </div>
        ) : (
          <div>
            <svg
              className="w-12 h-12 mx-auto text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="font-medium text-gray-700">
              Drop your bill PDF here, or click to browse
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Supports: National Grid electric bills (PDF)
            </p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Upload Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`px-6 py-2.5 rounded-lg font-medium text-sm transition-colors ${
            !file || uploading
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-brand-600 text-white hover:bg-brand-700"
          }`}
        >
          {uploading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Extracting...
            </span>
          ) : (
            "Extract Bill Data"
          )}
        </button>
      </div>
    </div>
  );
}
