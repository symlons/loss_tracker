/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SOCKET_HOSTING: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
