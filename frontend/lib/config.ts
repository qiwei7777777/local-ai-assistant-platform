function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

type ApiBaseUrlSource = "env" | "window" | "fallback";
type ApiMode = "same-origin" | "direct";
type ChatMode = "streaming" | "non_streaming";

function isLoopbackHost(hostname: string) {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

function getWindowHostname() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.location.hostname;
}

function getConfiguredApiBaseUrl() {
  const configuredValue = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configuredValue ? trimTrailingSlash(configuredValue) : null;
}

function getApiMode() {
  const configuredValue = getConfiguredApiBaseUrl();
  return configuredValue === "/api" ? ("same-origin" as ApiMode) : ("direct" as ApiMode);
}

function inferApiBaseUrlFromWindow() {
  if (typeof window === "undefined") {
    return null;
  }

  const { protocol, hostname } = window.location;
  if (!hostname) {
    return null;
  }

  return trimTrailingSlash(`${protocol}//${hostname}:8000`);
}

function resolveApiBaseUrl() {
  const configuredValue = getConfiguredApiBaseUrl();
  if (configuredValue) {
    return {
      value: configuredValue,
      source: "env" as ApiBaseUrlSource,
    };
  }

  const inferredValue = inferApiBaseUrlFromWindow();
  if (inferredValue) {
    return {
      value: inferredValue,
      source: "window" as ApiBaseUrlSource,
    };
  }

  return {
    value: "http://127.0.0.1:8000",
    source: "fallback" as ApiBaseUrlSource,
  };
}

function getApiBaseUrlWarning() {
  const configuredValue = getConfiguredApiBaseUrl();
  const browserHostname = getWindowHostname();

  if (!configuredValue || !browserHostname) {
    return null;
  }

  if (configuredValue === "/api") {
    return null;
  }

  try {
    const apiHostname = new URL(configuredValue).hostname;
    if (!isLoopbackHost(browserHostname) && isLoopbackHost(apiHostname)) {
      return "This page is opened from a LAN address, but NEXT_PUBLIC_API_BASE_URL still points to localhost/127.0.0.1. Restart the frontend after changing frontend/.env.local.";
    }
  } catch {
    return "NEXT_PUBLIC_API_BASE_URL is not a valid URL.";
  }

  return null;
}

export const appConfig = {
  appName:
    process.env.NEXT_PUBLIC_APP_NAME ?? "Local AI Assistant Platform",
  defaultModel:
    process.env.NEXT_PUBLIC_DEFAULT_MODEL ?? "gemma4:e4b",
  chatMode:
    process.env.NEXT_PUBLIC_CHAT_MODE === "non_streaming"
      ? ("non_streaming" as ChatMode)
      : ("streaming" as ChatMode),
  get apiMode() {
    return getApiMode();
  },
  get apiBaseUrl() {
    return resolveApiBaseUrl().value;
  },
  get apiBaseUrlSource() {
    return resolveApiBaseUrl().source;
  },
  get apiBaseUrlWarning() {
    return getApiBaseUrlWarning();
  },
};
