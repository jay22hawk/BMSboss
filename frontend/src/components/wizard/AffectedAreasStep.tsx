"use client";

import { useState } from "react";
import type { BMSCalculatorInput, AffectedArea } from "@/types";
import {
  VentilationType,
  HeatingSystemType,
  CoolingSystemType,
  TerminalUnitType,
} from "@/types";

interface AffectedAreasStepProps {
  data: BMSCalculatorInput;
  onChange: (updates: Partial<BMSCalculatorInput>) => void;
  onNext: () => void;
  onBack: () => void;
}

const SEQUENCES = [
  { key: "seq_system_schedules" as const, label: "System Schedules" },
  { key: "seq_optimal_start_stop" as const, label: "Optimal Start/Stop" },
  { key: "seq_reset_chilled_water" as const, label: "Reset Chilled Water Temp" },
  { key: "seq_reset_static_pressure" as const, label: "Reset Static Pressure" },
  { key: "seq_reset_boiler_water" as const, label: "Reset Boiler Water Temp" },
  { key: "seq_demand_control_ventilation" as const, label: "Demand Control Ventilation" },
  { key: "seq_economizer_control" as const, label: "Economizer Control" },
  { key: "seq_reset_supply_air_temp" as const, label: "Reset Supply Air Temp" },
  { key: "seq_reset_condenser_water" as const, label: "Reset Condenser Water Temp" },
];

function makeDefaultArea(num: number): AffectedArea {
  return {
    area_number: num,
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
}

export function AffectedAreasStep({
  data,
  onChange,
  onNext,
  onBack,
}: AffectedAreasStepProps) {
  const [activeTab, setActiveTab] = useState(0);
  const areas = data.affected_areas.length > 0
    ? data.affected_areas
    : [makeDefaultArea(1)];

  const updateArea = (index: number, updates: Partial<AffectedArea>) => {
    const newAreas = [...areas];
    newAreas[index] = { ...newAreas[index], ...updates };
    onChange({ affected_areas: newAreas });
  };

  const addArea = () => {
    if (areas.length < 5) {
      const newAreas = [...areas, makeDefaultArea(areas.length + 1)];
      onChange({ affected_areas: newAreas });
      setActiveTab(newAreas.length - 1);
    }
  };

  const removeArea = (index: number) => {
    if (areas.length > 1) {
      const newAreas = areas.filter((_, i) => i !== index).map((a, i) => ({
        ...a,
        area_number: i + 1,
      }));
      onChange({ affected_areas: newAreas });
      setActiveTab(Math.min(activeTab, newAreas.length - 1));
    }
  };

  const area = areas[activeTab];
  const totalSequences = SEQUENCES.reduce(
    (sum, s) => sum + (area[s.key] || 0),
    0,
  );

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Affected Areas & Sequences of Operation
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Define up to 5 building areas affected by the BMS project. For each
        area, specify the HVAC equipment and which sequences of operation will
        be implemented.
      </p>

      {/* Area Tabs */}
      <div className="flex items-center gap-2 mb-6">
        {areas.map((a, i) => (
          <button
            key={i}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${
              activeTab === i
                ? "bg-brand-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Area {i + 1}
          </button>
        ))}
        {areas.length < 5 && (
          <button
            onClick={addArea}
            className="px-3 py-2 text-sm rounded-lg bg-gray-100 text-gray-500 hover:bg-gray-200 transition-colors"
          >
            + Add Area
          </button>
        )}
      </div>

      {/* Active Area Form */}
      <div className="border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-gray-800">
            Area {activeTab + 1} Configuration
          </h3>
          {areas.length > 1 && (
            <button
              onClick={() => removeArea(activeTab)}
              className="text-xs text-red-500 hover:text-red-700 transition-colors"
            >
              Remove Area
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Area Description
            </label>
            <input
              type="text"
              value={area.area_description ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  area_description: e.target.value || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
              placeholder="e.g., Main Building, Wing A, Gymnasium"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Affected Square Footage <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={area.project_affected_sqft ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  project_affected_sqft: e.target.value
                    ? parseFloat(e.target.value)
                    : null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
              placeholder="e.g., 170353"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Equipment?
            </label>
            <select
              value={area.is_new_equipment ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  is_new_equipment: e.target.value || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            >
              <option value="">Select...</option>
              <option value="Unknown">Unknown</option>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ventilation Type
            </label>
            <select
              value={area.ventilation_type ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  ventilation_type:
                    (e.target.value as VentilationType) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            >
              <option value="">Select...</option>
              {Object.values(VentilationType).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Primary Heating System
            </label>
            <select
              value={area.primary_heating ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  primary_heating:
                    (e.target.value as HeatingSystemType) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            >
              <option value="">Select...</option>
              {Object.values(HeatingSystemType).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Primary Cooling System
            </label>
            <select
              value={area.primary_cooling ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  primary_cooling:
                    (e.target.value as CoolingSystemType) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            >
              <option value="">Select...</option>
              {Object.values(CoolingSystemType).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Terminal Unit Type
            </label>
            <select
              value={area.terminal_units ?? ""}
              onChange={(e) =>
                updateArea(activeTab, {
                  terminal_units:
                    (e.target.value as TerminalUnitType) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            >
              <option value="">Select...</option>
              {Object.values(TerminalUnitType).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Sequences of Operation */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-800 text-sm">
              Sequences of Operation
            </h4>
            <span className="text-sm text-brand-600 font-medium">
              {totalSequences} of 9 selected
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {SEQUENCES.map((seq) => (
              <label
                key={seq.key}
                className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                  area[seq.key]
                    ? "bg-brand-50 border-brand-300"
                    : "bg-gray-50 border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={area[seq.key] === 1}
                  onChange={(e) =>
                    updateArea(activeTab, {
                      [seq.key]: e.target.checked ? 1 : 0,
                    })
                  }
                  className="w-4 h-4 text-brand-600 rounded focus:ring-brand-500"
                />
                <span className="text-sm text-gray-700">{seq.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          &larr; Back
        </button>
        <button
          onClick={onNext}
          className="px-6 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors"
        >
          Review & Generate &rarr;
        </button>
      </div>
    </div>
  );
}
