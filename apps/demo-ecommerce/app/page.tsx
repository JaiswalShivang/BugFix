import Link from "next/link";

export default function Home() {
  return (
    <main style={{ maxWidth: 840, margin: "40px auto", padding: "0 24px" }}>
      <header style={{ borderBottom: "1px solid #e6ded3", paddingBottom: 24, marginBottom: 40 }}>
        <h1 style={{ fontSize: 26, letterSpacing: -0.5, fontWeight: 500 }}>Atelier Kinto</h1>
        <p style={{ color: "#7a7267", marginTop: 4 }}>Studio Ceramic Editions & Tableware</p>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginBottom: 40 }}>
        <div style={{ background: "#f2ece1", padding: 24, borderRadius: 2 }}>
          <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#685f54" strokeWidth="1.5">
              <path d="M4 19a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8H4v11zM2 5h20v3H2z"/>
            </svg>
          </div>
          <h2 style={{ fontSize: 18, marginTop: 16 }}>Dune Pour-Over Vessel</h2>
          <p style={{ color: "#7a7267", marginTop: 4 }}>$85.00 · Matte Sand Glaze</p>
        </div>
        <div style={{ background: "#f2ece1", padding: 24, borderRadius: 2 }}>
          <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#685f54" strokeWidth="1.5">
              <path d="M12 2a9 9 0 0 0-9 9c0 4.97 4.03 9 9 9s9-4.03 9-9a9 9 0 0 0-9-9zm0 4a5 5 0 1 1 0 10 5 5 0 0 1 0-10z"/>
            </svg>
          </div>
          <h2 style={{ fontSize: 18, marginTop: 16 }}>Kuro Stoneware Teacup</h2>
          <p style={{ color: "#7a7267", marginTop: 4 }}>$35.00 · Smoked Iron Finish</p>
        </div>
      </section>

      <div style={{ textAlign: "right" }}>
        <Link
          href="/checkout"
          style={{
            background: "#2b2621",
            color: "#faf7f2",
            padding: "12px 28px",
            textDecoration: "none",
            display: "inline-block",
            fontSize: 14,
            fontWeight: 500
          }}
        >
          Proceed to Checkout
        </Link>
      </div>
    </main>
  );
}
