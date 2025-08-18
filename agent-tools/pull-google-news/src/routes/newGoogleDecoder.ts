type DecodeResult = { status: true; decodedUrl: string } | { status: false; message: string };

function base64UrlToBuffer(b64url: string): Buffer {
  const pad = (4 - (b64url.length % 4)) % 4;
  return Buffer.from(b64url.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat(pad), 'base64');
}

function peelCandidate(buf: Buffer): string | null {
  const prefix = Buffer.from([0x08, 0x13, 0x22]);
  const suffix = Buffer.from([0xd2, 0x01, 0x00]);
  let start = buf.slice(0, prefix.length).equals(prefix) ? prefix.length : 0;
  let end = buf.slice(-suffix.length).equals(suffix) ? buf.length - suffix.length : buf.length;
  if (end - start < 2) return null;
  const core = buf.slice(start, end);
  const lenByte = core[0];
  const offset = lenByte >= 0x80 ? 2 : 1;
  const sliceEnd = Math.min(lenByte + 1, core.length);
  return core.slice(offset, sliceEnd).toString('utf8');
}

function extractToken(u: string): string | null {
  try {
    const url = new URL(u);
    const parts = url.pathname.split('/').filter(Boolean);
    if (parts.length >= 2 && (parts.at(-2) === 'articles' || parts.at(-2) === 'read')) return parts.at(-1)!;
    if (parts.length >= 3 && parts.at(-3) === 'rss' && parts.at(-2) === 'articles') return parts.at(-1)!;
    return null;
  } catch { return null; }
}

async function fetchSigTs(token: string): Promise<{ sig: string; ts: string } | null> {
  // Pull signed attributes from the public article page or its RSS variant
  const candidates = [
    `https://news.google.com/articles/${token}`,
    `https://news.google.com/read/${token}`,
    `https://news.google.com/rss/articles/${token}`,
  ];
  for (const url of candidates) {
    const r = await fetch(url);
    if (!r.ok) continue;
    const html = await r.text();
    const sig = html.match(/data-n-a-sg="([^"]+)"/)?.[1];
    const ts  = html.match(/data-n-a-ts="([^"]+)"/)?.[1];
    if (sig && ts) return { sig, ts };
  }
  return null;
}

async function decodeViaBatch(token: string, sig: string, ts: string): Promise<string> {
  const payload: [string, string] = [
    'Fbv4je',
    `["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"${token}",${ts},"${sig}"]`,
  ];
  const body = `f.req=${encodeURIComponent(JSON.stringify([[payload]]))}`;
  const resp = await fetch('https://news.google.com/_/DotsSplashUi/data/batchexecute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
    body,
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const text = await resp.text();
  const part = text.split('\n\n').find(p => { try { return Array.isArray(JSON.parse(p)); } catch { return false; } });
  if (!part) throw new Error('Unexpected response');
  const arr = JSON.parse(part);
  const inner = JSON.parse(arr[0][2]);
  const url = inner?.[1];
  if (typeof url !== 'string') throw new Error('URL not found');
  return url;
}

export async function decodeGoogleNewsUrl(sourceUrl: string): Promise<DecodeResult> {
  const token = extractToken(sourceUrl);
  if (!token) return { status: false, message: 'Not a recognized Google News URL' };
  const candidate = peelCandidate(base64UrlToBuffer(token));
  if (!candidate) return { status: false, message: 'Could not extract candidate URL' };
  if (!candidate.startsWith('AU_yqL')) return { status: true, decodedUrl: candidate };
  const sigts = await fetchSigTs(token);
  if (!sigts) return { status: false, message: 'Could not get signature/timestamp' };
  const finalUrl = await decodeViaBatch(token, sigts.sig, sigts.ts);
  return { status: true, decodedUrl: finalUrl };
}
