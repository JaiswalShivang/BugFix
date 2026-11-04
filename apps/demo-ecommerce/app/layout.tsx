import "./globals.css";
import React from "react";

export const metadata = {
  title: "Atelier Kinto — Handcrafted Stoneware",
  description: "Artisanal tableware and stoneware ceramics",
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

