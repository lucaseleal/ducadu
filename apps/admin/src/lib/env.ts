export function streamlitUrl(): string {
  return import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";
}

export function isProduction(): boolean {
  return import.meta.env.PROD;
}
