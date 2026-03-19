"use client";

import { useState, useCallback } from "react";
import type {
  WizardStep,
  ExtractedBillData,
  BMSCalculatorInput,
  AffectedArea,
  ExtractionResponse,
} from "@/types";
import { ProjectType, BuildingActivity, HeatingFuel } from "@/types";
import { UploadStep } from "@/components/wizard/UploadStep";
import { ReviewExtractionStep } from "@/components/wizard/ReviewExtractionStep";
import { BuildingInfoStep } from "@/components/wizard/BuildingInfoStep";
import { ProjectInfoStep } from "@/components/wizard/ProjectInfoStep";
import { AffectedAreasStep } from "@/components/wizard/AffectedAreasStep";
import { ReviewSubmitStep } from "@/components/wizard/ReviewSubmitStep";

const STEPS: { key: WizardStep; label: string }[] = [
  { key: "upload", label: "Upload Bill" },
  { key: "review-extraction", label: "Review Extraction" },
  { key: "building-info", label: "Building Info" },
  { key: "project-info", label: "Project Details" },
  { key: "affected-areas", label: "Affected Areas" },
  { key: "review-submit", label: "Review & Generate" },
];

const DEFAULT_AREA: AffectedArea = {
  area_number: 1,
  project_affected_sqft: null,
  area_description: null,
  is_new_equipment: null,
  ventilation_type: null,
  primary_heating: null,
  primary_cooling: null,
  terminal_units: null,
  secondary_heating_to_hp: null,
  seq_system_schedules: 0,
  seq_optimal_start_stop: 0,
  seq_reset_chilled_water: 0,
  seq_reset_static_pressure: 0,
  seq_reset_boiler_water: 0,
  seq_demand_control_ventilation: 0,
  seq_economizer_control: 0,
  seq_reset_supply_air_temp: 0,
  seq_reset_condenser_water: 0,
  opt_cooling: 0,
  opt_ventilation: 0,
  opt_heating: 0,
};

const DEFAULT_CALC_INPUT: BMSCalculatorInput = {
  company_name: null,
  company_address: null,
  company_city: null,
  electric_account: null,
  gas_account: null,
  electric_pa: null,
  gas_pa: null,
  customer_contact_name: null,
  customer_phone: null,
  building_activity: null,
  heating_fuel: null,
  total_building_sqft: null,
  annual_electric_kwh: null,
  annual_fuel_usage: null,
  project_type: null,
  demand_response_curtailment: null,
  bms_manufacturer: null,
  total_project_cost: null,
  notes: null,
  affected_areas: [{ ...DEFAULT_AREA }],
};

export default function NewSubmissionPage() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("upload");
  const [extractionData, setExtractionData] =
    useState<ExtractedBillData | null>(null);
  const [extractionWarnings, setExtractionWarnings] = useState<string[]>([]);
  const [calcInput, setCalcInput] =
    useState<BMSCalculatorInput>(DEFAULT_CALC_INPUT);

  const currentStepIndex = STEPS.findIndex((s) => s.key === currentStep);

  const goNext = () => {
    if (currentStepIndex < STEPS.length - 1) {
      setCurrentStep(STEPS[currentStepIndex + 1].key);
    }
  };

  const goBack = () => {
    if (currentStepIndex > 0) {
      setCurrentStep(STEPS[currentStepIndex - 1].key);
    }
  };

  const handleExtractionComplete = useCallback(
    (data: ExtractedBillData, merged: BMSCalculatorInput | null, warnings: string[]) => {
      setExtractionData(data);
      setExtractionWarnings(warnings);
      if (merged) {
        setCalcInput((prev) => ({
          ...prev,
          ...merged,
          affected_areas: prev.affected_areas.length
            ? prev.affected_areas
            : [{ ...DEFAULT_AREA }],
        }));
      }
      setCurrentStep("review-extraction");
    },
    [],
  );

  const updateCalcInput = useCallback(
    (updates: Partial<BMSCalculatorInput>) => {
      setCalcInput((prev) => ({ ...prev, ...updates }));
    },
    [],
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Step Progress */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {STEPS.map((step, idx) => (
            <div
              key={step.key}
              className="flex items-center"
              style={{ flex: idx < STEPS.length - 1 ? 1 : 0 }}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  idx < currentStepIndex
                    ? "bg-green-500 text-white"
                    : idx === currentStepIndex
                      ? "bg-brand-600 text-white"
                      : "bg-gray-200 text-gray-500"
                }`}
              >
                {idx < currentStepIndex ? (
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 ${
                    idx < currentStepIndex ? "bg-green-500" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between">
          {STEPS.map((step) => (
            <span
              key={step.key}
              className={`text-xs ${
                step.key === currentStep
                  ? "text-brand-600 font-medium"
                  : "text-gray-400"
              }`}
            >
              {step.label}
            </span>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 min-h-[400px]">
        {currentStep === "upload" && (
          <UploadStep onComplete={handleExtractionComplete} />
        )}
        {currentStep === "review-extraction" && extractionData && (
          <ReviewExtractionStep
            data={extractionData}
            warnings={extractionWarnings}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === "building-info" && (
          <BuildingInfoStep
            data={calcInput}
            onChange={updateCalcInput}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === "project-info" && (
          <ProjectInfoStep
            data={calcInput}
            onChange={updateCalcInput}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === "affected-areas" && (
          <AffectedAreasStep
            data={calcInput}
            onChange={updateCalcInput}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === "review-submit" && (
          <ReviewSubmitStep
            extraction={extractionData}
            calcInput={calcInput}
            onBack={goBack}
          />
        )}
      </div>
    </div>
  );
}
