import test from "node:test";
import assert from "node:assert/strict";
import { findCouponByCode } from "../lib/coupons";

test("findCouponByCode returns coupon for valid SAVE20", async () => {
  const coupon = await findCouponByCode("SAVE20");
  assert.ok(coupon);
  assert.equal(coupon.discount, 20);
  assert.equal(coupon.expired, false);
});

test("findCouponByCode returns null for EXPIRED10", async () => {
  const coupon = await findCouponByCode("EXPIRED10");
  assert.equal(coupon, null);
});

test("findCouponByCode returns null for empty or invalid code", async () => {
  assert.equal(await findCouponByCode(""), null);
  assert.equal(await findCouponByCode("NONEXISTENT"), null);
});
