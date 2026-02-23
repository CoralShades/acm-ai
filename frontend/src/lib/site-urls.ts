const DEFAULT_MARKETING_URL = "https://vaea.coralshades.ai";

const normalizedMarketingUrl = (
  process.env.NEXT_PUBLIC_MARKETING_URL?.trim() || DEFAULT_MARKETING_URL
).replace(/\/+$/, "");

export const MARKETING_URL = normalizedMarketingUrl;
export const MARKETING_DOCS_URL = `${normalizedMarketingUrl}/docs`;
