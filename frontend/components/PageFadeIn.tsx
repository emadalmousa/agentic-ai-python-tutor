"use client"

import { useEffect, useRef } from "react"
import { usePathname } from "next/navigation"

export default function PageFadeIn({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  const pathname = usePathname()

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.opacity = "0"
    el.style.transform = "translateY(8px)"
    const raf = requestAnimationFrame(() => {
      el.style.transition = "opacity 0.45s ease, transform 0.45s ease"
      el.style.opacity = "1"
      el.style.transform = "translateY(0)"
    })
    return () => cancelAnimationFrame(raf)
  }, [pathname])

  return (
    <div ref={ref} className="flex-1 flex flex-col overflow-hidden min-h-0">
      {children}
    </div>
  )
}
