'use client'

import { usePathname } from 'next/navigation'

// The header and footer are shared; only the homepage uses the reviewed wording.
export default function HomepageText({ home, standard }: { home: string; standard: string }) {
  return usePathname() === '/' ? home : standard
}
