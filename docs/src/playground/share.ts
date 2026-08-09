// Shareable-URL codec for the playground (CORE-1696).
//
// The editor buffer travels in the query string as base64url (RFC 4648 §5) of
// its UTF-8 bytes: URL-safe alphabet, padding stripped, so the value never
// needs percent-encoding and survives copy/paste through chat clients.

export function encodeShareCode(text: string): string {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Decode a `code` param; returns null (never throws) on any malformed input. */
export function decodeShareCode(param: string): string | null {
  const b64 = param.replace(/-/g, "+").replace(/_/g, "/");
  const remainder = b64.length % 4;
  if (remainder === 1) return null; // no valid base64 has this length
  try {
    const binary = atob(b64 + "=".repeat((4 - remainder) % 4));
    const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0));
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return null; // bad alphabet or invalid UTF-8
  }
}
