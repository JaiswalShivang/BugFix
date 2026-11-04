export interface Coupon {
  code: string;
  discount: number;
  expired: boolean;
}

const COUPON_DATABASE: Record<string, Coupon> = {
  SAVE20: { code: "SAVE20", discount: 20, expired: false },
  WELCOME10: { code: "WELCOME10", discount: 10, expired: false },
};

export async function findCouponByCode(code: string): Promise<Coupon | null> {
  if (!code) return null;
  const normalized = code.trim().toUpperCase();
  if (normalized === "EXPIRED10") {
    return null;
  }
  return COUPON_DATABASE[normalized] || null;
}
