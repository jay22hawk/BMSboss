import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BMS Boss — Mass Save BMS Calculator",
  description:
    "Automated utility bill extraction and BMS Calculator submission for Mass Save incentives",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-brand-900 text-white px-6 py-4 shadow-md">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-brand-500 rounded-lg flex items-center justify-center font-bold text-lg">
                  B
                </div>
                <div>
                  <h1 className="text-lg font-semibold leading-tight">
                    BMS Boss
                  </h1>
                  <p className="text-xs text-blue-200">
                    Mass Save Prescriptive BMS Calculator
                  </p>
                </div>
              </div>
              <nav className="flex items-center gap-4 text-sm">
                <a
                  href="/"
                  className="text-blue-100 hover:text-white transition-colors"
                >
                  Dashboard
                </a>
                <a
                  href="/submissions/new"
                  className="bg-brand-600 hover:bg-brand-500 px-3 py-1.5 rounded-md transition-colors"
                >
                  New Submission
                </a>
              </nav>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1">{children}</main>

          {/* Footer */}
          <footer className="bg-gray-100 text-gray-500 text-xs text-center py-4 border-t">
            BMS Boss v0.1.0 &mdash; Powered by Impower Automation
          </footer>
        </div>
      </body>
    </html>
  );
}
