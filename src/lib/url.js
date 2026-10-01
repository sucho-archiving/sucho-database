const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

export const url = (path) => `${BASE}${path}`;

export const authorityUrl = (id) => url(`/Archives/Authorities/${id}/`);
export const resourceUrl = (id) => url(`/Archives/Resources/${id}/`);
export const waybackUrl = (collectionUrl) =>
  `https://web.archive.org/web/20220000000000*/${collectionUrl}`;
