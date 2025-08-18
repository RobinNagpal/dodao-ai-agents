// resolve-final-url.ts
import puppeteer, {
  Browser,
  HTTPResponse,
  Page,
  PuppeteerLaunchOptions,
  Protocol,
} from "puppeteer";

type ResourceType =
  | "document" | "stylesheet" | "image" | "media" | "font" | "script"
  | "texttrack" | "xhr" | "fetch" | "eventsource" | "websocket"
  | "manifest" | "other";

export interface ResolveOptions {
  /** Puppeteer launch options (you can pass executablePath, args, etc.) */
  launch?: PuppeteerLaunchOptions;
  /** Navigation timeout for the initial goto (ms). Default: 15_000 */
  gotoTimeoutMs?: number;
  /**
   * Per-hop wait for *additional* navigations (to catch meta/JS redirects), ms.
   * Default: 4_000
   */
  extraNavWaitMs?: number;
  /** Max extra navigations (client-side hops). Default: 4 */
  maxHops?: number;
  /**
   * Block non-essential resources to speed things up.
   * Default: true (blocks images, media, fonts, stylesheets)
   */
  blockNonEssential?: boolean;
  /** Optional user agent override. */
  userAgent?: string;
}

export interface RedirectHop {
  /** URL that was requested at this hop (pre-redirect URL) */
  url: string;
  /** HTTP status code for this hop (if available). Null when Puppeteer can't provide it. */
  status: number | null;
  /** Redirect response Location header (if available) */
  location: string | null;
}

export interface ResolveResult {
  ok: true;
  /** Final URL after all redirects */
  finalUrl: string;
  /** Server-side redirect chain derived from the initial navigation */
  serverRedirects: RedirectHop[];
  /** How we detected the final URL */
  source: "server" | "client" | "none";
}

export interface ResolveError {
  ok: false;
  error: string;
  serverRedirects: RedirectHop[];
}

/**
 * Resolve final URL after server and client/meta/script redirects using Puppeteer (headless).
 * - Uses `page.goto` (follows server redirects).
 * - Then waits for additional navigations briefly to catch client/meta redirects.
 */
export async function resolveFinalUrlWithPuppeteer(
  inputUrl: string,
  options: ResolveOptions = {}
): Promise<ResolveResult | ResolveError> {
  const gotoTimeoutMs: number = options.gotoTimeoutMs ?? 15_000;
  const extraNavWaitMs: number = options.extraNavWaitMs ?? 4_000;
  const maxHops: number = options.maxHops ?? 4;
  const blockNonEssential: boolean = options.blockNonEssential ?? true;

  // Sensible defaults for headless mode; you can override via options.launch
  const launchOpts: PuppeteerLaunchOptions = {
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    ...options.launch,
  };

  let browser: Browser | null = null;
  const serverRedirects: RedirectHop[] = [];

  try {
    browser = await puppeteer.launch(launchOpts);
    const page: Page = await browser.newPage();

    if (options.userAgent) {
      await page.setUserAgent(options.userAgent);
    }

    if (blockNonEssential) {
      await page.setRequestInterception(true);
      page.on("request", (req) => {
        const type = req.resourceType() as ResourceType;
        // Keep "document", "script", "xhr", "fetch" to allow client redirects.
        const block: ReadonlySet<ResourceType> = new Set<ResourceType>([
          "image",
          "stylesheet",
          "font",
          "media",
          "other",
          "manifest",
          "texttrack",
          "eventsource",
          "websocket",
        ]);
        if (block.has(type)) {
          void req.abort();
        } else {
          void req.continue();
        }
      });
    }

    // Initial navigation (follows server redirects)
    const initialResponse: HTTPResponse | null = await page.goto(inputUrl, {
      waitUntil: "domcontentloaded",
      timeout: gotoTimeoutMs,
    });

    // Build server-side redirect chain (if any)
    if (initialResponse) {
      // Puppeteer gives us the chain *leading to* the final response
      const chain = initialResponse.request().redirectChain();
      // The chain excludes the final response; we append it for completeness
      const chainResponses: Array<{ url: string; resp: HTTPResponse | null }> =
        chain.map((req) => ({ url: req.url(), resp: req.response() }));

      chainResponses.push({ url: initialResponse.url(), resp: initialResponse });

      // Convert to RedirectHop[] (best-effort for Location header)
      for (let i = 0; i < chainResponses.length - 1; i += 1) {
        const current = chainResponses[i];
        const next = chainResponses[i + 1];

        const status: number | null = current.resp ? current.resp.status() : null;
        let location: string | null = null;
        if (current.resp) {
          const headers = current.resp.headers();
          location = headers["location"] ?? null;
        }

        serverRedirects.push({
          url: current.url,
          status,
          location: location ?? (next ? next.url : null),
        });
      }
    }

    // At this point, `page.url()` is the final URL after server redirects.
    // Now catch *client/meta/JS* redirects by waiting for additional navigations.
    // We'll loop small waits to handle chains like: landing -> meta-refresh -> JS redirect, etc.
    let lastUrl: string = page.url();
    let source: ResolveResult["source"] = serverRedirects.length > 0 ? "server" : "none";

    for (let hop = 0; hop < maxHops; hop += 1) {
      try {
        const nav = await page.waitForNavigation({
          waitUntil: "domcontentloaded",
          timeout: extraNavWaitMs,
        });
        if (!nav) break;
        const currentUrl: string = page.url();
        if (currentUrl !== lastUrl) {
          lastUrl = currentUrl;
          source = source === "server" ? "server" : "client";
          // continue to see if there are more client redirects
          continue;
        }
        // If URL didn't change, stop.
        break;
      } catch {
        // Timed out waiting for more client-side navigation
        break;
      }
    }

    return {
      ok: true,
      finalUrl: lastUrl,
      serverRedirects,
      source,
    };
  } catch (err) {
    const message: string =
      err instanceof Error ? err.message : String(err);
    return {
      ok: false,
      error: message,
      serverRedirects,
    };
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}
