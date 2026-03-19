"use client";

import type { BMSCalculatorInput } from "@/types";
import { ProjectType } from "@/types";

interface ProjectInfoStepProps {
  data: BMSCalculatorInput;
  onChange: (updates: Partial<BMSCalculatorInput>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function ProjectInfoStep({
  data,
  onChange,
  onNext,
  onBack,
}: ProjectInfoStepProps) {
  const isSubscription = data.project_type === ProjectType.SUBSCRIPTION;

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Project Details
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter the BMS control system and project details for this submission.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Project Type <span className="text-red-500">*</span>
          </label>
          <select
            value={data.project_type ?? ""}
            onChange={(e) =>
              onChange({
                project_type: (e.target.value as ProjectType) || null,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none bg-white"
          >
            <option value="">Select project type...</option>
            {Object.values(ProjectType).map((val) => (
              <option key={val} value={val}>
                {val}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-400">
            Determines the incentive rate: New BMS ($0.10/sqft/seq), Upgrade
            ($0.05), Subscription ($0.01)
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Demand Response / Curtailment
          </label>
          <select
            value={data.demand_response_curtailment ?? ""}
            onChange={(e) =>
              onChange({
                demand_response_curtailment: e.target.value || null,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none bg-white"
          >
            <option value="">Select...</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            BMS Manufacturer
          </label>
          <input
            type="text"
            value={data.bms_manufacturer ?? ""}
            onChange={(e) =>
              onChange({ bms_manufacturer: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="e.g., Honeywell, Johnson Controls, Siemens"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Total Project Cost ($) <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={data.total_project_cost ?? ""}
            onChange={(e) =>
              onChange({
                total_project_cost: e.target.value
                  ? parseFloat(e.target.value)
                  : null,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="e.g., 100000"
          />
          <p className="mt-1 text-xs text-gray-400">
            Incentive is capped at 60% of total project cost
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            PA Technical Representative
          </label>
          <input
            type="text"
            value={data.pa_technical_rep ?? ""}
            onChange={(e) =>
              onChange({ pa_technical_rep: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="Technical rep name"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            PA Tech Rep Phone
          </label>
          <input
            type="tel"
            value={data.pa_tech_rep_phone ?? ""}
            onChange={(e) =>
              onChange({ pa_tech_rep_phone: e.target.value || null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            placeholder="(555) 555-1234"
          />
        </div>
      </div>

      {/* Subscription-specific fields */}
      {isSubscription && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="font-medium text-gray-800 mb-4">
            Subscription Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Product
              </label>
              <input
                type="text"
                value={data.subscription_product ?? ""}
                onChange={(e) =>
                  onChange({
                    subscription_product: e.target.value || null,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                placeholder="Product name"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Years
              </label>
              <input
                type="number"
                value={data.subscription_years ?? ""}
                onChange={(e) =>
                  onChange({
                    subscription_years: e.target.value
                      ? parseInt(e.target.value)
                      : null,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                placeholder="e.g., 3"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Installation Cost ($)
              </label>
              <input
                type="number"
                value={data.subscription_install_cost ?? ""}
                onChange={(e) =>
                  onChange({
                    subscription_install_cost: e.target.value
                      ? parseFloat(e.target.value)
                      : null,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                placeholder="One-time installation cost"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Annual Fee ($)
              </label>
              <input
                type="number"
                value={data.subscription_annual_fee ?? ""}
                onChange={(e) =>
                  onChange({
                    subscription_annual_fee: e.target.value
                      ? parseFloat(e.target.value)
                      : null,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                placeholder="Annual subscription fee"
              />
            </div>
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="mt-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={data.notes ?? ""}
          onChange={(e) => onChange({ notes: e.target.value || null })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none resize-none"
          placeholder="Any additional notes about the project..."
        />
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
          Continue to Affected Areas &rarr;
        </button>
      </div>
    </div>
  );
}
