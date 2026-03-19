"use client";

import type { ExtractedBillData } from "@/types";

interface ReviewExtractionStepProps {
  data: ExtractedBillData;
  warnings: string[];
  onNext: () => void;
  onBack: () => void;
}

function DataRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number | null | undefined;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100">
      <span className="text-sm text-gray-600">{label}</span>
      <span
        className={`text-sm font-medium ${
          highlight ? "text-brand-700" : "text-gray-900"
        }`}
      >
        {value ?? "—"}
      </span>
    </div>
  );
}

export function ReviewExtractionStep({
  data,
  warnings,
  onNext,
  onBack,
}: ReviewExtractionStepProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Extraction Results
          </h2>
          <p className="text-sm text-gray-500">
            Review the data extracted from your bill. Confidence:{" "}
            <span className="font-medium text-green-600">
              {(data.confidence_score * 100).toFixed(0)}%
            </span>
          </p>
        </div>
        <div className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
          {data.utility_sponsor}
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          {warnings.map((w, i) => (
            <p key={i} className="text-sm text-yellow-700">
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Extracted Data Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Account Info */}
        <div>
          <h3 className="font-medium text-gray-800 mb-2 text-sm uppercase tracking-wide">
            Account Information
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <DataRow label="Customer" value={data.customer_name} highlight />
            <DataRow label="Account #" value={data.account_number} />
            <DataRow label="Meter #" value={data.meter_number} />
            <DataRow label="Service Address" value={data.service_address} />
            <DataRow
              label="City/State/Zip"
              value={
                data.service_city
                  ? `${data.service_city}, ${data.service_state} ${data.service_zip}`
                  : null
              }
            />
          </div>
        </div>

        {/* Billing Period */}
        <div>
          <h3 className="font-medium text-gray-800 mb-2 text-sm uppercase tracking-wide">
            Billing Details
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <DataRow
              label="Period"
              value={
                data.billing_period_start
                  ? `${data.billing_period_start} to ${data.billing_period_end}`
                  : null
              }
            />
            <DataRow label="Days" value={data.days_in_period} />
            <DataRow label="Bill Date" value={data.bill_date} />
            <DataRow label="Rate" value={data.rate_type} />
            <DataRow label="Load Zone" value={data.load_zone} />
            <DataRow label="Voltage" value={data.voltage_level} />
          </div>
        </div>

        {/* Usage */}
        <div>
          <h3 className="font-medium text-gray-800 mb-2 text-sm uppercase tracking-wide">
            Energy Usage
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <DataRow
              label="Total Energy"
              value={
                data.total_energy_kwh
                  ? `${data.total_energy_kwh.toLocaleString()} kWh`
                  : null
              }
              highlight
            />
            <DataRow
              label="Meter Multiplier"
              value={data.meter_multiplier}
            />
            {data.usage_readings.map((r, i) => (
              <DataRow
                key={i}
                label={r.type_of_service}
                value={`${r.total_usage.toLocaleString()} kWh`}
              />
            ))}
          </div>
        </div>

        {/* Demand & Charges */}
        <div>
          <h3 className="font-medium text-gray-800 mb-2 text-sm uppercase tracking-wide">
            Demand & Charges
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <DataRow
              label="Peak Demand (kW)"
              value={data.demand_kw?.peak}
            />
            <DataRow
              label="Off-Peak Demand (kW)"
              value={data.demand_kw?.off_peak}
            />
            <DataRow
              label="Delivery Charges"
              value={
                data.total_delivery_charges
                  ? `$${data.total_delivery_charges.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                  : null
              }
            />
            <DataRow
              label="Supply Charges"
              value={
                data.total_supply_charges
                  ? `$${data.total_supply_charges.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                  : null
              }
            />
            <DataRow
              label="Supplier"
              value={data.supplier_name}
            />
          </div>
        </div>
      </div>

      {/* 12-Month History */}
      {data.monthly_usage_history.length > 0 && (
        <div className="mt-6">
          <h3 className="font-medium text-gray-800 mb-2 text-sm uppercase tracking-wide">
            12-Month Usage History &mdash; Annual Total:{" "}
            <span className="text-brand-700">
              {data.annual_usage_kwh?.toLocaleString()} kWh
            </span>
          </h3>
          <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-3 md:grid-cols-4 gap-2">
            {data.monthly_usage_history.map((m, i) => (
              <div key={i} className="text-center p-2 bg-white rounded border border-gray-100">
                <div className="text-xs text-gray-500">{m.month}</div>
                <div className="text-sm font-medium">
                  {m.kwh.toLocaleString()}
                </div>
              </div>
            ))}
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
        <button
          onClick={onNext}
          className="px-6 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors"
        >
          Continue to Building Info &rarr;
        </button>
      </div>
    </div>
  );
}
