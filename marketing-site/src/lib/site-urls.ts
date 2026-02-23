const DEFAULT_APP_URL = "https://demo.vaea.coralshades.ai";

export const APP_URL =
  process.env.NEXT_PUBLIC_APP_URL?.trim() || DEFAULT_APP_URL;
