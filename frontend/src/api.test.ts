import { afterEach, describe, expect, it, vi } from "vitest";

import { getProducts, RequestError } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API errors", () => {
  it("preserves the backend error code and field details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "validation_error",
            message: "Correct the highlighted fields.",
            details: [
              {
                field: "competitor_items.0.brand",
                message: "Enter a competitor brand.",
              },
            ],
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const error = await getProducts().catch((reason: unknown) => reason);

    expect(error).toBeInstanceOf(RequestError);
    expect(error).toMatchObject({
      status: 422,
      code: "validation_error",
      details: [
        {
          field: "competitor_items.0.brand",
          message: "Enter a competitor brand.",
        },
      ],
    });
  });

  it("uses a safe fallback for a non-JSON server error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Unavailable", { status: 503 })),
    );

    const error = await getProducts().catch((reason: unknown) => reason);

    expect(error).toMatchObject({
      message: "The request could not be completed.",
      status: 503,
      code: "request_failed",
      details: [],
    });
  });
});
