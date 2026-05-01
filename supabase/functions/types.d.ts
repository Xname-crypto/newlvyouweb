declare module 'jsr:@supabase/supabase-js@2' {
  export function createClient(url: string, key: string): any
}

declare module 'npm:openai@4.24.1' {
  const OpenAI: any
  export default OpenAI
}

declare const Deno: {
  serve: (handler: (req: Request) => Promise<Response> | Response) => void
  env: { get: (k: string) => string | undefined }
}
