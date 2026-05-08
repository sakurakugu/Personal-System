declare module 'reading-time/lib/reading-time' {
  import type { Options, ReadTimeResults } from 'reading-time'

  export default function readingTime(text: string, options?: Options): ReadTimeResults
}
