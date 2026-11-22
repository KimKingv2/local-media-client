const API_ORIGIN = "https://api.themoviedb.org";
const IMAGE_ORIGIN = "https://image.tmdb.org";
const IMAGE_SIZES = new Set(["w92", "w154", "w185", "w342", "w500", "w780", "w1280", "original"]);

function corsHeaders(extra = {}) {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Accept, Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
    ...extra,
  };
}

function response(body, status = 200, headers = {}) {
  return new Response(body, {
    status,
    headers: corsHeaders(headers),
  });
}

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    if (request.method === "OPTIONS") {
      return response(null, 204);
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return response("Method not allowed", 405, { "Allow": "GET, HEAD, OPTIONS" });
    }
    if (incoming.pathname === "/health") {
      return response(JSON.stringify({ ok: true, service: "fixed-upstream-tmdb-proxy" }), 200, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
      });
    }

    let upstream;
    const headers = new Headers({ "Accept": request.headers.get("Accept") || "*/*" });
    let cacheControl = "no-store";

    if (incoming.pathname.startsWith("/3/")) {
      const token = request.headers.get("Authorization");
      if (!token || !/^Bearer\s+\S+$/i.test(token)) {
        return response("Missing Bearer token", 401, { "Cache-Control": "no-store" });
      }
      upstream = new URL(incoming.pathname + incoming.search, API_ORIGIN);
      headers.set("Authorization", token);
      headers.set("Accept", "application/json");
    } else if (incoming.pathname.startsWith("/image/t/p/")) {
      const relative = incoming.pathname.slice("/image/t/p/".length);
      const [size, ...fileParts] = relative.split("/");
      const filePath = fileParts.join("/");
      if (!IMAGE_SIZES.has(size) || !filePath || filePath.includes("..") || filePath.includes("\\")) {
        return response("Invalid image path", 400, { "Cache-Control": "no-store" });
      }
      upstream = new URL("/t/p/" + size + "/" + filePath, IMAGE_ORIGIN);
      cacheControl = "public, max-age=86400, stale-while-revalidate=604800";
    } else {
      return response("Not found", 404, { "Cache-Control": "no-store" });
    }

    try {
      const upstreamResponse = await fetch(upstream.toString(), {
        method: request.method,
        headers,
        redirect: "follow",
      });
      const outHeaders = new Headers();
      for (const name of ["content-type", "content-length", "etag", "last-modified"]) {
        const value = upstreamResponse.headers.get(name);
        if (value) outHeaders.set(name, value);
      }
      outHeaders.set("Cache-Control", cacheControl);
      return new Response(request.method === "HEAD" ? null : upstreamResponse.body, {
        status: upstreamResponse.status,
        statusText: upstreamResponse.statusText,
        headers: corsHeaders(Object.fromEntries(outHeaders.entries())),
      });
    } catch {
      return response("Upstream request failed", 502, { "Cache-Control": "no-store" });
    }
  },
};
