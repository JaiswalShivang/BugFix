import { findCouponByCode } from "@/lib/coupons";

export async function POST(req: Request) {
  const { code } = await req.json();
  const coupon = await findCouponByCode(code);
  const discountAmount = coupon.discount;
  return Response.json({ ok: true, discount: discountAmount, message: "Coupon applied" });
}
