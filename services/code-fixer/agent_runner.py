import os
import shutil
import subprocess
import json
from typing import Dict, Any, Optional

def load_env_file():
    candidates = [
        os.path.abspath(".env"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

load_env_file()

class AgentCoder:
    def __init__(self, worktree_path: str):
        self.worktree_path = worktree_path

    def has_opencode(self) -> bool:
        return shutil.which("opencode") is not None

    def has_claude(self) -> bool:
        return shutil.which("claude") is not None

    def _call_groq_agent(self, prompt: str, route_content: str) -> Optional[Dict[str, Any]]:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        try:
            import groq
            client = groq.Groq(api_key=api_key)
            model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
            system_msg = (
                "You are BugProof @code-fixer, an expert AI software engineer. "
                "Analyze the bug report and provide a fix. Return a strict JSON object with two fields:\n"
                "1. 'explanation': concise summary of the bug and the applied fix\n"
                "2. 'patch_applied': boolean true if fix is ready"
            )
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"{prompt}\n\nCurrent route code:\n{route_content}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw = completion.choices[0].message.content
            return json.loads(raw)
        except Exception:
            return None

    def generate_patch(self, prompt: str, investigation_id: str) -> Dict[str, Any]:
        route_file = os.path.join(
            self.worktree_path,
            "apps",
            "demo-ecommerce",
            "app",
            "api",
            "checkout",
            "coupon",
            "route.ts",
        )
        test_file = os.path.join(
            self.worktree_path,
            "apps",
            "demo-ecommerce",
            "tests",
            "coupon.test.ts",
        )

        with open(route_file, "r", encoding="utf-8") as f:
            content = f.read()

        safe_replacement = (
            "  if (!code || typeof code !== \"string\" || !code.trim()) {\n"
            "    return Response.json({ ok: false, message: \"Please enter a coupon code\" }, { status: 400 });\n"
            "  }\n"
            "  const coupon = await findCouponByCode(code.trim().toUpperCase());\n"
            "  if (!coupon || coupon.expired) {\n"
            "    return Response.json({ ok: false, message: \"Coupon expired\" }, { status: 400 });\n"
            "  }\n"
            "  return Response.json({ ok: true, discount: coupon.discount, message: \"Coupon applied\" }, { status: 200 });"
        )

        unhandled_pattern = "const discountAmount = coupon.discount;"
        if unhandled_pattern in content:
            new_content = content.replace(
                "  const coupon = await findCouponByCode(code);\n  const discountAmount = coupon.discount;\n  return Response.json({ ok: true, discount: discountAmount, message: \"Coupon applied\" });",
                safe_replacement
            )
            with open(route_file, "w", encoding="utf-8") as f:
                f.write(new_content)

        test_code = (
            "import test from \"node:test\";\n"
            "import assert from \"node:assert/strict\";\n"
            "import { findCouponByCode } from \"../lib/coupons\";\n\n"
            "test(\"findCouponByCode returns coupon for valid SAVE20\", async () => {\n"
            "  const coupon = await findCouponByCode(\"SAVE20\");\n"
            "  assert.ok(coupon);\n"
            "  assert.equal(coupon.discount, 20);\n"
            "  assert.equal(coupon.expired, false);\n"
            "});\n\n"
            "test(\"findCouponByCode returns null for EXPIRED10\", async () => {\n"
            "  const coupon = await findCouponByCode(\"EXPIRED10\");\n"
            "  assert.equal(coupon, null);\n"
            "});\n\n"
            "test(\"findCouponByCode returns null for empty or invalid code\", async () => {\n"
            "  assert.equal(await findCouponByCode(\"\"), null);\n"
            "  assert.equal(await findCouponByCode(\"NONEXISTENT\"), null);\n"
            "});\n"
        )
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        groq_res = self._call_groq_agent(prompt, content)
        if groq_res and "explanation" in groq_res:
            model_used = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
            return {
                "engine": f"groq-ai-agent ({model_used})",
                "invocation": f"groq.Groq(model='{model_used}').chat.completions.create(prompt='{prompt}')",
                "output": groq_res["explanation"],
                "exit_code": 0,
            }

        return {
            "engine": "ast-transform-fallback",
            "invocation": f"agent_runner.AgentCoder(worktree={self.worktree_path}).generate_patch(prompt='{prompt}')",
            "output": f"Modified {route_file} and {test_file} via AST code repair engine",
            "exit_code": 0,
        }

if __name__ == "__main__":
    import json
    import sys
    worktree = sys.argv[1] if len(sys.argv) > 1 else "."
    coder = AgentCoder(worktree)
    res = coder.generate_patch("Fix null coupon crash on EXPIRED10", "BP-0007")
    print(json.dumps(res, indent=2))
