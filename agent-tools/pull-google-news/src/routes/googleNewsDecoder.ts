// googleNewsDecoder.ts
// Node 18+/Bun/Deno compatible (uses global fetch).
// No external deps. Optional proxy agent can be passed via RequestInit if you need proxies.

type DecodeResult =
  | { status: true; decodedUrl: string }
  | { status: false; message: string };

interface DecodeOptions {
  /** Delay in seconds (used by the Python lib to avoid rate limits). Optional. */
  intervalSeconds?: number;
  /**
   * Extra fetch options (e.g., { agent } for Node proxies, headers overrides, etc.).
   * If you need an HTTP(S) proxy in Node, create an agent with `https-proxy-agent`
   * and pass it here: { agent: new HttpsProxyAgent("http://user:pass@host:port") }
   */
  fetchInit?: RequestInit;
}

const GNEWS_HOST = "news.google.com";

/** Extracts the base64 token from a Google News URL */
export function extractTokenFromGoogleNewsUrl(sourceUrl: string):
  | { ok: true; token: string }
  | { ok: false; reason: string }
{
  try {
    const u = new URL(sourceUrl);
    if (u.hostname !== GNEWS_HOST) return { ok: false, reason: "Not a news.google.com URL." };

    // paths like /articles/<token> or /read/<token> or /rss/articles/<token>
    const parts = u.pathname.split("/").filter(Boolean);
    if (parts.length < 2) return { ok: false, reason: "Unexpected path format." };

    // acceptable patterns: ["articles", token], ["read", token], ["rss","articles", token]
    const penultimate = parts.at(-2);
    if (penultimate === "articles" || penultimate === "read") {
      return { ok: true, token: parts.at(-1)! };
    }

    // rss/articles/<token>
    if (parts.length >= 3 && parts[parts.length - 3] === "rss" && parts[parts.length - 2] === "articles") {
      return { ok: true, token: parts.at(-1)! };
    }

    return { ok: false, reason: "Not a recognized Google News article/read URL." };
  } catch (e: any) {
    return { ok: false, reason: `Bad URL: ${e?.message ?? String(e)}` };
  }
}

function base64UrlToBuffer(b64url: string): Buffer {
  const padLen = (4 - (b64url.length % 4)) % 4;
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat(padLen);
  return Buffer.from(b64, "base64");
}

/**
 * Mirrors the Python logic:
 *  - strip optional prefix 08 13 22
 *  - strip optional suffix D2 01 00
 *  - read first byte as "length"; if >= 0x80, assume 2-byte varint and start at offset 2
 *  - slice [offset, length+1) and return that as string
 */
function peelUrlCandidateFromDecodedBlob(decoded: Buffer): string | null {
  const prefix = Buffer.from([0x08, 0x13, 0x22]);
  const suffix = Buffer.from([0xd2, 0x01, 0x00]);

  let start = 0;
  let end = decoded.length;

  // strip prefix
  if (decoded.slice(0, prefix.length).equals(prefix)) start += prefix.length;

  // strip suffix
  if (decoded.slice(end - suffix.length, end).equals(suffix)) end -= suffix.length;

  if (end - start < 2) return null;
  const core = decoded.slice(start, end);

  const first = core[0];
  if (first === undefined) return null;

  // Python version treats the first byte itself as "length"
  const urlLenByte = first; // (yes, even if >= 0x80)
  const offset = first >= 0x80 ? 2 : 1;

  if (core.length < offset) return null;

  // Slice end is exclusive; Python used [offset : length+1]
  const sliceEnd = Math.min(urlLenByte + 1, core.length);
  const body = core.slice(offset, sliceEnd);

  // The URL is ASCII; decode as UTF-8 is fine because it's pure ASCII bytes.
  return body.toString("utf8");
}

// ------------------------------
// "New" path: token requires batch call (AU_yqL…)
// ------------------------------

async function fetchSignatureAndTimestamp(
  token: string,
  init?: RequestInit
): Promise<{ ok: true; sig: string; ts: string } | { ok: false; reason: string }> {
  // Try /articles/<token> then fallback to /rss/articles/<token>
  const candidates = [
    `https://${GNEWS_HOST}/articles/${token}`,
    `https://${GNEWS_HOST}/rss/articles/${token}`,
  ];

  const tryOne = async (url: string) => {
    const r = await fetch(url, init);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const html = await r.text();

    // Minimal, robust-ish attribute extraction (no full DOM parser):
    const sigMatch = html.match(/data-n-a-sg="([^"]+)"/);
    const tsMatch = html.match(/data-n-a-ts="([^"]+)"/);
    const sig = sigMatch?.[1];
    const ts = tsMatch?.[1];
    if (sig && ts) return { sig, ts };
    throw new Error("Signature or timestamp not found in page.");
  };

  for (const url of candidates) {
    try {
      const { sig, ts } = await tryOne(url);
      return { ok: true, sig, ts };
    } catch (e) {
      // continue to fallback
    }
  }
  return { ok: false, reason: "Failed to get signature/timestamp from Google News page." };
}

async function decodeViaBatchExecute(
  token: string,
  sig: string,
  ts: string,
  init?: RequestInit
): Promise<DecodeResult> {
  // Mirrors the Python envelope:
  // payload = [
  //   "Fbv4je",
  //   `["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"${token}",${timestamp},"${signature}"]`
  // ]
  const payload: [string, string] = [
    "Fbv4je",
    `["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"${token}",${ts},"${sig}"]`,
  ];

  const body = `f.req=${encodeURIComponent(JSON.stringify([[payload]]))}`;
  const resp = await fetch(
    `https://${GNEWS_HOST}/_/DotsSplashUi/data/batchexecute`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
          "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
      },
      body,
      ...init,
    }
  );

  if (!resp.ok) {
    return { status: false, message: `Batch request failed: HTTP ${resp.status}` };
  }

  const text = await resp.text();

  // The response is a weird "JSON in a JSON-ish envelope" separated by \n\n.
  // Python uses: json.loads(text.split("\n\n")[1])[:-2] then another JSON.parse of [0][2].
  try {
    const parts = text.split("\n\n");
    // Heuristic: find the first line that parses as JSON array
    let jsonLine: any = null;
    for (const p of parts) {
      try {
        const tmp = JSON.parse(p);
        if (Array.isArray(tmp)) {
          jsonLine = tmp;
          break;
        }
      } catch {
        // ignore
      }
    }
    if (!jsonLine) throw new Error("Could not locate JSON payload");

    // Follow the same indexing as the Python code
    const trimmed = jsonLine.slice(0, -2); // drop last two entries
    const inner = trimmed?.[0]?.[2];
    const asJson = typeof inner === "string" ? JSON.parse(inner) : inner;
    const finalUrl = asJson?.[1];

    if (typeof finalUrl !== "string") {
      throw new Error("Final URL not found in payload");
    }
    return { status: true, decodedUrl: finalUrl };
  } catch (e: any) {
    return { status: false, message: `Batch payload parse error: ${e?.message ?? e}` };
  }
}

// ------------------------------
// Public API
// ------------------------------

export async function decodeGoogleNewsUrl(
  sourceUrl: string,
  opts: DecodeOptions = {}
): Promise<DecodeResult> {
  try {
    const tok = extractTokenFromGoogleNewsUrl(sourceUrl);
    if (!tok.ok) return { status: false, message: tok.reason };
    const token = tok.token;

    // Step 1: decode token → candidate URL
    const decoded = base64UrlToBuffer(token);
    const candidate = peelUrlCandidateFromDecodedBlob(decoded);
    if (!candidate) return { status: false, message: "Could not peel candidate URL from token." };

    // Step 2: If candidate looks like a real URL and not the special marker, return it
    if (!candidate.startsWith("AU_yqL")) {
      if (opts.intervalSeconds) {
        await new Promise(r => setTimeout(r, (opts.intervalSeconds || 10) * 1000));
      }
      return { status: true, decodedUrl: candidate };
    }

    // Step 3: "AU_yqL..." → need signature & timestamp, then batch execute
    const sigTs = await fetchSignatureAndTimestamp(token, opts.fetchInit);
    if (!sigTs.ok) return { status: false, message: sigTs.reason };

    const res = await decodeViaBatchExecute(token, sigTs.sig, sigTs.ts, opts.fetchInit);
    if (opts.intervalSeconds) {
      await new Promise(r => setTimeout(r, (opts.intervalSeconds || 10) * 1000));
    }
    return res;
  } catch (e: any) {
    return { status: false, message: e?.message ?? String(e) };
  }
}

/** Convenience: decode many at once (keeps order). */
export async function decodeGoogleNewsUrls(
  urls: string[],
  opts: DecodeOptions = {}
): Promise<DecodeResult[]> {
  const out: DecodeResult[] = [];
  for (const u of urls) {
    out.push(await decodeGoogleNewsUrl(u, opts));
  }
  return out;
}

// ------------------------------
// Example usage:
// ------------------------------
/*
(async () => {
  const url = "https://news.google.com/read/CBMikgFBVV95cUxNQWY1aHBScmdfYkExVkhkUW8zeGI4UXBVejJ4eUM2UTJxWF9wc21DZVJqNHJCNTB1NnpDRVQwcUdVdk9jdHVPSGRJSXNRZ2Fuc21CTUktclZJbTlxQUJfV2dmMGVDUWJrbzJNeWFmdUFlRzJmZ1JNbWVtUkR1RDJETUx1cFJiVGNIa1pJeU1TMENOZw?hl=en-CA&gl=CA&ceid=CA%3Aen";
  const res = await decodeGoogleNewsUrl(url);
  console.log(res);
})();
*/
