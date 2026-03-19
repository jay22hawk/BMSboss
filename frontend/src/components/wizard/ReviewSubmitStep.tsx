"use client";

import { useState } from "react";
import type { ExtractedBillData, BMSCalculatorInput } from "@/types";
import { generateExcel, getDownloadUrl } from "@/lib/api";

interface ReviewSubmitStepProps {
  extraction: ExtractedBillData | null;
  calcInput: BMSCalculatorInput;
  onBack: () => void;
}

const SEQUENCE_LABELS: Record<string, string> = {
  seq_system_schedules: "System Schedules",
  seq_optimal_start_stop: "Optimal Start/Stop",
  seq_reset_chilled_water: "Reset Chilled Water Temp",
  seq_reset_static_pressure: "Reset Static Pressure",
  seq_reset_boiler_water: "Reset Boiler Water Temp",
  seq_demand_control_ventilation: "Demand Control Ventilation",
  seq_economizer_control: "Economizer Control",
  seq_reset_supply_air_temp: "Reset Supply Air Temp",
  seq_reset_condenser_water: "Reset Condenser Water Temp",
};

export function ReviewSubmitStep({
  extraction,
  calcInput,
  onBack,
}: ReviewSubmitStepProps) {
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [incentiveEstimate, setIncentiveEstimate] = useState<number | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);

    try {
      const result = await generateExcel(calcInput);
      if (result.success && result.file_path) {
        const fileId = result.file_path.split("/").pop() || "";
        setDownloadUrl(getDownloadUrl(fileId));
        setIncentiveEstimate(result.incentive_estimate);
      } else {
        setError(result.errors?.join("; ") || "Generation failed.");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect to generation service.",
      );
    } finally {
      setGenerating(false);
    }
  };

  // Compute summary stats
  const totalAffectedSqft = calcInput.affected_areas.reduce(
    (sum, a) => sum + (a.project_affected_sqft || 0),
    0,
  );
  const totalSequences = calcInput.affected_areas.reduce((sum, a) => {
    return (
      sum +
      Object.keys(SEQUENCE_LABELS).reduce(
        (s, key) => s + ((a as any)[key] || 0),
        0,
      )
    );
  }, 0);

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Review & Generate
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Review your submission details below, then generate the BMS Calculator
        Excel file.
      </p>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Building Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-800 mb-3 text-sm uppercase tracking-wide">
            Building
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Name</span>
              <span className="font-medium">{calcInput.company_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Address</span>
              <span className="font-medium">
                {calcInput.company_address || "—"}
                {calcInput.company_city ? `, ${calcInput.company_city}` : ""}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Type</span>
              <span className="font-medium">
                {calcInput.building_activity || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Total sqft</span>
              <span className="font-medium">
                {calcInput.total_building_sqft?.toLocaleString() || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Annual Electric</span>
              <span className="font-medium">
                {calcInput.annual_electric_kwh
                  ? `${calcInput.annual_electric_kwh.toLocaleString()} kWh`
                  : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Electric Account</span>
              <span className="font-medium">
                {calcInput.electric_account || "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Project Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-800 mb-3 text-sm uppercase tracking-wide">
            Project
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Project Type</span>
              <span className="font-medium">
                {calcInput.project_type || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">BMS Manufacturer</span>
              <span className="font-medium">
                {calcInput.bms_manufacturer || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Total Project Cost</span>
              <span className="font-medium">
                {calcInput.total_project_cost
                  ? `$${calcInput.total_project_cost.toLocaleString()}`
                  : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Areas</span>
              <span className="font-medium">
                {calcInput.affected_areas.length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Total Affected sqft</span>
              <span className="font-medium">
                {totalAffectedSqft.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Total Sequences</span>
              <span className="font-medium">{totalSequences}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Affected Areas Detail */}
      <div className="mb-6">
        <h3 className="font-medium text-gray-800 mb-3 text-sm uppercase tracking-wide">
          Affected Areas
        </h3>
        {calcInput.affected_areas.map((area, i) => {
          const activeSeqs = Object.entries(SEQUENCE_LABELS)
            .filter(([key]) => (area as any)[key] === 1)
            .map(([, label]) => label);

          return (
            <div
              key={i}
              className="bg-gray-50 rounded-lg p-4 mb-2 text-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-800">
                  Area {area.area_number}
                  {area.area_description
                    ? ` — ${area.area_description}`
                    : ""}
                </span>
                <span className="text-gray-500">
                  {area.project_affected_sqft?.toLocaleString() || "—"} sqft
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {activeSeqs.map((s) => (
                  <span
                    key={s}
                    className="px-2 py-0.5 bg-brand-100 text-brand-700 rounded text-xs font-medium"
                  >
                    {s}
                  </span>
                ))}
                {activeSeqs.length === 0 && (
                  <span className="text-gray-400 text-xs">
                    No sequences selected
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Success / Download */}
      {downloadUrl && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-xl">
          <div className="flex items-center gap-3">
            <svg
              className="w-8 h-8 text-green-500 flex-shrink-0"
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
            <div className="flex-1">
              <p className="font-medium text-green-800">
                BMS Calculator Generated Successfully
              </p>
              {incentiveEstimate !== null && (
                <p className="text-sm text-green-600 mt-0.5">
                  Estimated Incentive:{" "}
                  <span className="font-semibold">
                    ${incentiveEstimate.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </p>
              )}
            </div>
            <a
              href={downloadUrl}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            >
              Download .xlsx
            </a>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          &larr; Back
        </button>
        {!downloadUrl && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              generating
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-green-600 text-white hover:bg-green-700"
            }`}
          >
            {generating ? (
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
                Generating...
              </span>
            ) : (
              "Generate BMS Calculator .xlsx"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
