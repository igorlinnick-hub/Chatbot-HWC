import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/sidebar";
import { cookies } from "next/headers";

export const metadata: Metadata = {
  title: "Hawaii Wellness — Bot Dashboard",
  description: "Control centre for the Hawaii Wellness Clinic intake chatbot",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // The login page renders without sidebar by having its own full-height layout;
  // we detect via a cookie-based heuristic. Simplest: always render sidebar for
  // authenticated routes, and let /login override via its own full-bleed JSX.
  const authed = Boolean(cookies().get("dashboard_auth")?.value) || !process.env.DASHBOARD_PASSWORD;
  return (
    <html lang="en">
      <body>
        {authed ? (
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 min-w-0 p-6 md:p-10 max-w-full">{children}</main>
          </div>
        ) : (
          children
        )}
      </body>
    </html>
  );
}
