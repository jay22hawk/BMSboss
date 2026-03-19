"use client";

import type { BMSCalculatorInput } from "@/types";
import { BuildingActivity, HeatingFuel } from "@/types";

interface BuildingInfoStepProps {
  data: BMSCalculatorInput;
  onChange: (updates: Partial<BMSCalculatorInput>) => void;
  onNext: () => void;
  onBack: () => void;
}

function FormField({
  label,
  required,
  children,
  hint,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
      {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  );
}

export function BuildingInfoStep({
  data,
  onChange,
  onNext,
  onBack,
}: BuildingInfoStepProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Building Information
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter the building details for the BMS Calculator. Fields marked with
        * are required. Some fields may have been auto-filled from the bill.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        {/* Company / Customer Info */}
        <FormField label="Company / Building Name" required>
          <input
            type="text"
            value={data.company_name ?? ""}
            onChange={(e) => onChange({ company_name: e.target.value || null })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="e.g., Murdock Middle High School"
          />
        </FormField>

        <FormField label="Contact Name">
          <input
            type="text"
            value={data.customer_contact_name ?? ""}
            onChange={(e) =>
              onChange({ customer_contact_name: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="Primary contact for this project"
          />
        </FormField>

        <FormField label="Street Address">
          <input
            type="text"
            value={data.company_address ?? ""}
            onChange={(e) =>
              onChange({ company_address: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="32 Elmwood Rd"
          />
        </FormField>

        <FormField label="City">
          <input
            type="text"
            value={data.company_city ?? ""}
            onChange={(e) =>
              onChange({ company_city: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="Winchendon"
          />
        </FormField>

        <FormField label="Contact Phone">
          <input
            type="tel"
            value={data.customer_phone ?? ""}
            onChange={(e) =>
              onChange({ customer_phone: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="(555) 555-1234"
          />
        </FormField>

        <FormField label="Electric Account #">
          <input
            type="text"
            value={data.electric_account ?? ""}
            onChange={(e) =>
              onChange({ electric_account: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-blue-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="Auto-filled from bill"
          />
        </FormField>

        <FormField label="Gas Account # (if applicable)">
          <input
            type="text"
            value={data.gas_account ?? ""}
            onChange={(e) =>
              onChange({ gas_account: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="Gas account number"
          />
        </FormField>

        <FormField label="Electric PA (Program Administrator)">
          <select
            value={data.electric_pa ?? ""}
            onChange={(e) =>
              onChange({ electric_pa: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none bg-white"
          >
            <option value="">Select...</option>
            <option value="National Grid">National Grid</option>
            <option value="Eversource">Eversource</option>
            <option value="Liberty">Liberty</option>
            <option value="Cape Light Compact">Cape Light Compact</option>
            <option value="Berkshire Gas">Berkshire Gas</option>
            <option value="Unitil">Unitil</option>
          </select>
        </FormField>
      </div>

      {/* Building Details Section */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="font-medium text-gray-800 mb-4">
          Building Energy Profile
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
          <FormField label="Building Activity Type" required>
            <select
              value={data.building_activity ?? ""}
              onChange={(e) =>
                onChange({
                  building_activity:
                    (e.target.value as BuildingActivity) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none bg-white"
            >
              <option value="">Select building type...</option>
              {Object.values(BuildingActivity).map((val) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Primary Heating Fuel" required>
            <select
              value={data.heating_fuel ?? ""}
              onChange={(e) =>
                onChange({
                  heating_fuel: (e.target.value as HeatingFuel) || null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none bg-white"
            >
              <option value="">Select fuel type...</option>
              {Object.values(HeatingFuel).map((val) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
          </FormField>

          <FormField
            label="Total Building Area (sqft)"
            required
            hint="Max 300,000 sqft for Prescriptive BMS program"
          >
            <input
              type="number"
              value={data.total_building_sqft ?? ""}
              onChange={(e) =>
                onChange({
                  total_building_sqft: e.target.value
                    ? parseFloat(e.target.value)
                    : null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
              placeholder="e.g., 170353"
              max={300000}
            />
            {data.total_building_sqft &&
              data.total_building_sqft > 300000 && (
                <p className="mt-1 text-xs text-red-500">
                  Exceeds 300,000 sqft limit for prescriptive BMS program
                </p>
              )}
          </FormField>

          <FormField
            label="Annual Electric Usage (kWh)"
            hint="Auto-calculated from 12-month bill history if available"
          >
            <input
              type="number"
              value={data.annual_electric_kwh ?? ""}
              onChange={(e) =>
                onChange({
                  annual_electric_kwh: e.target.value
                    ? parseFloat(e.target.value)
                    : null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-blue-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
              placeholder="Auto-filled from bill"
            />
          </FormField>

          <FormField label="Annual Fuel Usage (therms, if applicable)">
            <input
              type="number"
              value={data.annual_fuel_usage ?? ""}
              onChange={(e) =>
                onChange({
                  annual_fuel_usage: e.target.value
                    ? parseFloat(e.target.value)
                    : null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
              placeholder="e.g., 15000"
            />
          </FormField>
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
          Continue to Project Details &rarr;
        </button>
      </div>
    </div>
  );
}
