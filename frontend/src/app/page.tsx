"use client";

import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      {/* Welcome */}
      <div className="mb-10">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to BMS Boss
        </h2>
        <p className="text-gray-600 max-w-2xl">
          Upload utility energy bills, auto-extract data, and generate completed
          Prescriptive BMS Calculator spreadsheets for Mass Save incentive
          submissions.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <Link
          href="/submissions/new"
          className="block p-6 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-brand-500 transition-all group"
        >
          <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-100 transition-colors">
            <svg
              className="w-6 h-6 text-brand-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">New Submission</h3>
          <p className="text-sm text-gray-500">
            Upload a bill PDF and create a new BMS Calculator submission
          </p>
        </Link>

        <div className="block p-6 bg-white rounded-xl border border-gray-200 shadow-sm opacity-60">
          <div className="w-12 h-12 bg-gray-50 rounded-lg flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">
            Submissions
            <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              Coming Soon
            </span>
          </h3>
          <p className="text-sm text-gray-500">
            View and manage past submissions across customers and locations
          </p>
        </div>

        <div className="block p-6 bg-white rounded-xl border border-gray-200 shadow-sm opacity-60">
          <div className="w-12 h-12 bg-gray-50 rounded-lg flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">
            Customers
            <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              Coming Soon
            </span>
          </h3>
          <p className="text-sm text-gray-500">
            Manage customers, locations, and their BMS submission history
          </p>
        </div>
      </div>

      {/* Supported Sponsors */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">
          Supported Utility Sponsors
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-sm font-medium text-green-800">
              National Grid
            </span>
          </div>
          {["Eversource", "Liberty", "Cape Light Compact", "Berkshire Gas", "Unitil"].map(
            (name) => (
              <div
                key={name}
                className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="w-2 h-2 bg-gray-300 rounded-full" />
                <span className="text-sm text-gray-500">{name}</span>
              </div>
            ),
          )}
        </div>
      </div>
    </div>
  );
}
