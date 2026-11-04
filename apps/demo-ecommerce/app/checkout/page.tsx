"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function CheckoutPage() {
  const [couponCode, setCouponCode] = useState("");
  const [discountPercent, setDiscountPercent] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);
  const [isServerError, setIsServerError] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const subtotal = 120.0;
  const discountAmount = (subtotal * discountPercent) / 100;
  const total = subtotal - discountAmount;

  async function handleApplyCoupon(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setIsError(false);
    setIsServerError(false);

    if (!couponCode || !couponCode.trim()) {
      setIsError(true);
      setMessage("Please enter a coupon code");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/checkout/coupon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: couponCode }),
      });

      if (res.status >= 500) {
        setIsServerError(true);
        setIsError(true);
        setMessage("Internal Server Error");
        console.error("HTTP 500: Failed to apply coupon " + couponCode);
        return;
      }

      const data = await res.json();
      if (!res.ok || !data.ok) {
        setIsError(true);
        setMessage(data.message || "Coupon expired");
      } else {
        setIsError(false);
        setDiscountPercent(data.discount || 0);
        setMessage(data.message || "Coupon applied");
      }
    } catch (err) {
      setIsServerError(true);
      setIsError(true);
      setMessage("Internal Server Error");
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 760, margin: "32px auto", padding: "0 24px" }}>
      <header style={{ marginBottom: 32, borderBottom: "1px solid #e6ded3", paddingBottom: 16 }}>
        <Link href="/" style={{ color: "#7a7267", textDecoration: "none", fontSize: 13, textTransform: "uppercase", letterSpacing: 1 }}>
          ← Atelier Kinto Studio
        </Link>
        <h1 style={{ fontSize: 24, marginTop: 8, fontWeight: 500 }}>Checkout</h1>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 36 }}>
        <section>
          <h2 style={{ fontSize: 16, marginBottom: 16, fontWeight: 600 }}>Order Summary</h2>
          <div style={{ border: "1px solid #e6ded3", background: "#fbf9f5", padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span>Dune Pour-Over Vessel</span>
              <span>$85.00</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <span>Kuro Stoneware Teacup</span>
              <span>$35.00</span>
            </div>

            <div style={{ borderTop: "1px solid #e6ded3", paddingTop: 12, marginTop: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, color: "#6b675e" }}>
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              {discountPercent > 0 && (
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, color: "#2f6f5e" }}>
                  <span>Discount ({discountPercent}%)</span>
                  <span>-${discountAmount.toFixed(2)}</span>
                </div>
              )}
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 18, fontWeight: 600, borderTop: "1px solid #e6ded3", paddingTop: 12, marginTop: 8 }}>
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 style={{ fontSize: 16, marginBottom: 16, fontWeight: 600 }}>Payment & Promotion</h2>
          
          <form onSubmit={handleApplyCoupon} style={{ marginBottom: 24 }}>
            <div style={{ marginBottom: 12 }}>
              <label
                htmlFor="coupon-code"
                style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 6, color: "#47423b" }}
              >
                Coupon code
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  id="coupon-code"
                  name="coupon"
                  aria-label="Coupon code"
                  type="text"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  placeholder="Enter promo code"
                  style={{
                    flex: 1,
                    padding: "10px 12px",
                    border: "1px solid #d4ccbd",
                    fontSize: 14,
                    background: "#ffffff",
                    outline: "none"
                  }}
                />
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    background: "#2b2621",
                    color: "#ffffff",
                    border: "none",
                    padding: "10px 16px",
                    fontSize: 13,
                    cursor: "pointer",
                    fontWeight: 500
                  }}
                >
                  Apply coupon
                </button>
              </div>
            </div>

            {message && (
              <div
                style={{
                  marginTop: 10,
                  padding: "8px 12px",
                  fontSize: 13,
                  border: isError ? "1px solid #c8402a" : "1px solid #2f6f5e",
                  color: isError ? "#c8402a" : "#2f6f5e",
                  background: isError ? "#fcf0ed" : "#eef7f4"
                }}
              >
                {message}
              </div>
            )}
            {isServerError && (
              <div style={{ marginTop: 8, fontSize: 12, color: "#c8402a", fontWeight: 600 }}>
                Internal Server Error
              </div>
            )}
          </form>

          <div style={{ borderTop: "1px solid #e6ded3", paddingTop: 20 }}>
            <button
              type="button"
              style={{
                width: "100%",
                background: "#6b6255",
                color: "#ffffff",
                border: "none",
                padding: "12px",
                fontSize: 14,
                cursor: "pointer",
                fontWeight: 600
              }}
            >
              Complete Order
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
