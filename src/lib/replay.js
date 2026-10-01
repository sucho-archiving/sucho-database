import { url as siteUrl } from "./url.js";

const ARCHIVE_FILE = /\.(wacz|warc|warc\.gz)$/i;

function parse(link, fallbackUrl) {
  if (!link) return null;
  let u;
  try {
    u = new URL(link);
  } catch {
    return null;
  }
  const source = u.searchParams.get("source");
  if (source) {
    const hash = new URLSearchParams(u.hash.slice(1));
    return { source, url: hash.get("url") || fallbackUrl };
  }
  if (ARCHIVE_FILE.test(u.pathname)) return { source: link, url: fallbackUrl };
  return null;
}


export function replaySource(r) {
  return parse(r.wacz_url, r.collection_url) ?? parse(r.wacz_file, r.collection_url);
}


export const replayPageUrl = (id) => siteUrl(`/Archives/Resources/${id}/replay/`);


export function externalReplayUrl(r) {
  const s = replaySource(r);
  if (!s) return null;
  if (r.wacz_url?.includes("replayweb.page")) return r.wacz_url;
  return `https://replayweb.page/?source=${encodeURIComponent(s.source)}#view=pages&url=${encodeURIComponent(s.url)}`;
}
