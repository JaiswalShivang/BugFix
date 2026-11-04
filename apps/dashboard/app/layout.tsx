import "./globals.css";
import React from "react";

export const metadata = {
  title: "BugProof — Forensic Case File & Evidence Mirror",
  description: "Evidence-Based AI Debugging and Verification Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
