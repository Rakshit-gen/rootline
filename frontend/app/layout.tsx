import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "rootline",
  description: "Agentic incident investigation with a ranked, evidence-backed root-cause trace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
