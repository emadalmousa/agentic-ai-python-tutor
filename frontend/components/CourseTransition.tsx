"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"

interface Props {
  onDone: () => void
}

export default function CourseTransition({ onDone }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const router = useRouter()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D
    if (!ctx) return

    let animId: number
    let startTime: number | null = null

    // Resize canvas
    function resize() {
      if (!canvas) return
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener("resize", resize)

    // --- Particles ---
    const NUM_PARTICLES = 60
    type Particle = {
      x: number; y: number
      vx: number; vy: number
      radius: number
      alpha: number
      color: string
    }
    const COLORS = ["#6366f1", "#8b5cf6", "#3b82f6", "#a78bfa", "#60a5fa"]

    function makeParticle(): Particle {
      return {
        x: Math.random() * (canvas?.width ?? 800),
        y: Math.random() * (canvas?.height ?? 600),
        vx: (Math.random() - 0.5) * 1.2,
        vy: (Math.random() - 0.5) * 1.2,
        radius: Math.random() * 2.5 + 0.8,
        alpha: Math.random() * 0.5 + 0.2,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      }
    }
    const particles: Particle[] = Array.from({ length: NUM_PARTICLES }, makeParticle)

    // --- Rocket ---
    // Phases (ms): 0-600 idle glow-in, 600-2200 fly across, 2200-2800 fade out + navigate
    const PHASE_IDLE = 600
    const PHASE_FLY_END = 2200
    const PHASE_TOTAL = 2700

    function easeInOutCubic(t: number) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
    }
    function easeOutExpo(t: number) {
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
    }

    // Trail history
    const trail: { x: number; y: number; t: number }[] = []

    function drawRocket(
      ctx: CanvasRenderingContext2D,
      cx: number, cy: number,
      scale: number, alpha: number, angle: number
    ) {
      ctx.save()
      ctx.globalAlpha = alpha
      ctx.translate(cx, cy)
      ctx.rotate(angle)
      ctx.scale(scale, scale)

      // Body
      const grad = ctx.createLinearGradient(-22, 0, 22, 0)
      grad.addColorStop(0, "#818cf8")
      grad.addColorStop(0.5, "#e0e7ff")
      grad.addColorStop(1, "#6366f1")
      ctx.beginPath()
      ctx.moveTo(22, 0)
      ctx.quadraticCurveTo(10, -10, -12, -8)
      ctx.lineTo(-12, 8)
      ctx.quadraticCurveTo(10, 10, 22, 0)
      ctx.fillStyle = grad
      ctx.fill()

      // Window
      ctx.beginPath()
      ctx.arc(6, 0, 4.5, 0, Math.PI * 2)
      ctx.fillStyle = "#bfdbfe"
      ctx.fill()
      ctx.beginPath()
      ctx.arc(6, 0, 4.5, 0, Math.PI * 2)
      ctx.strokeStyle = "#6366f1"
      ctx.lineWidth = 1
      ctx.stroke()

      // Fins
      ctx.beginPath()
      ctx.moveTo(-12, -8)
      ctx.lineTo(-20, -18)
      ctx.lineTo(-8, -8)
      ctx.fillStyle = "#a5b4fc"
      ctx.fill()
      ctx.beginPath()
      ctx.moveTo(-12, 8)
      ctx.lineTo(-20, 18)
      ctx.lineTo(-8, 8)
      ctx.fillStyle = "#a5b4fc"
      ctx.fill()

      ctx.restore()
    }

    function drawFlame(
      ctx: CanvasRenderingContext2D,
      cx: number, cy: number,
      scale: number, alpha: number, angle: number, t: number
    ) {
      ctx.save()
      ctx.globalAlpha = alpha * 0.9
      ctx.translate(cx, cy)
      ctx.rotate(angle)
      ctx.scale(scale, scale)

      const flicker = 1 + Math.sin(t * 0.05) * 0.15
      const grad = ctx.createRadialGradient(-18, 0, 0, -28 * flicker, 0, 14)
      grad.addColorStop(0, "#fbbf24")
      grad.addColorStop(0.4, "#f97316")
      grad.addColorStop(1, "rgba(239,68,68,0)")
      ctx.beginPath()
      ctx.ellipse(-22 * flicker, 0, 14 * flicker, 6, 0, 0, Math.PI * 2)
      ctx.fillStyle = grad
      ctx.fill()

      // Inner white core
      ctx.globalAlpha = alpha * 0.6
      ctx.beginPath()
      ctx.ellipse(-17, 0, 5 * flicker, 2.5, 0, 0, Math.PI * 2)
      ctx.fillStyle = "#fef9c3"
      ctx.fill()

      ctx.restore()
    }

    function drawTrail(ctx: CanvasRenderingContext2D, now: number) {
      for (let i = trail.length - 1; i >= 0; i--) {
        const age = now - trail[i].t
        const maxAge = 600
        if (age > maxAge) { trail.splice(0, i + 1); break }
        const a = (1 - age / maxAge) * 0.25
        const r = (1 - age / maxAge) * 3
        ctx.beginPath()
        ctx.arc(trail[i].x, trail[i].y, r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(139,92,246,${a})`
        ctx.fill()
      }
    }

    let navigated = false

    function frame(ts: number) {
      if (!startTime) startTime = ts
      const elapsed = ts - startTime
      const W = canvas!.width, H = canvas!.height

      ctx.clearRect(0, 0, W, H)

      // Background
      const bgGrad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.7)
      bgGrad.addColorStop(0, "#0f172a")
      bgGrad.addColorStop(1, "#060e1c")
      ctx.fillStyle = bgGrad
      ctx.fillRect(0, 0, W, H)

      // Particles
      for (const p of particles) {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0) p.x = W
        if (p.x > W) p.x = 0
        if (p.y < 0) p.y = H
        if (p.y > H) p.y = 0
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.alpha
        ctx.fill()
      }
      ctx.globalAlpha = 1

      // Central glow ring (idle phase)
      if (elapsed < PHASE_IDLE + 200) {
        const glowT = Math.min(elapsed / PHASE_IDLE, 1)
        const glowAlpha = easeInOutCubic(glowT) * 0.15
        const glowGrad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, 200)
        glowGrad.addColorStop(0, `rgba(99,102,241,${glowAlpha})`)
        glowGrad.addColorStop(1, "transparent")
        ctx.fillStyle = glowGrad
        ctx.fillRect(0, 0, W, H)
      }

      // Rocket flight
      if (elapsed >= PHASE_IDLE && elapsed <= PHASE_TOTAL) {
        const flyProgress = Math.min((elapsed - PHASE_IDLE) / (PHASE_FLY_END - PHASE_IDLE), 1)
        const easedFly = easeOutExpo(flyProgress)

        // Fly from left-center to right-off-screen
        const startX = -60
        const endX = W + 100
        const startY = H / 2 + 30
        const endY = H / 2 - 60
        const cx = startX + (endX - startX) * easedFly
        const cy = startY + (endY - startY) * easedFly
        const angle = Math.atan2(endY - startY, endX - startX)

        // Scale: grow from 0.6 to 1.4 then shrink as it leaves
        const scaleIn = flyProgress < 0.1 ? easeInOutCubic(flyProgress / 0.1) * 0.8 + 0.6 : 1.4
        const scaleOut = flyProgress > 0.85 ? 1.4 - easeInOutCubic((flyProgress - 0.85) / 0.15) * 0.8 : 1.4
        const scale = Math.min(scaleIn, scaleOut)

        // Alpha: fade in + fade out
        const fadeIn = flyProgress < 0.08 ? flyProgress / 0.08 : 1
        const fadeOut = flyProgress > 0.88 ? 1 - (flyProgress - 0.88) / 0.12 : 1
        const rocketAlpha = fadeIn * fadeOut

        // Motion blur trail
        if (flyProgress < 0.95) {
          trail.push({ x: cx, y: cy, t: elapsed })
        }
        drawTrail(ctx, elapsed)

        // Glow around rocket
        const glowR = 80 * scale
        const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowR)
        glow.addColorStop(0, `rgba(99,102,241,${0.18 * rocketAlpha})`)
        glow.addColorStop(1, "transparent")
        ctx.fillStyle = glow
        ctx.globalAlpha = 1
        ctx.fillRect(0, 0, W, H)

        drawFlame(ctx, cx, cy, scale, rocketAlpha, angle, elapsed)
        drawRocket(ctx, cx, cy, scale, rocketAlpha, angle)

        // Navigate when rocket exits screen
        if (flyProgress >= 1 && !navigated) {
          navigated = true
          setTimeout(() => {
            onDone()
            router.push("/progress")
          }, 120)
        }
      }

      // Text
      const textAlpha = elapsed < PHASE_IDLE
        ? easeInOutCubic(elapsed / PHASE_IDLE)
        : elapsed > PHASE_FLY_END - 200
          ? Math.max(0, 1 - (elapsed - (PHASE_FLY_END - 200)) / 300)
          : 1

      ctx.globalAlpha = textAlpha
      ctx.textAlign = "center"

      ctx.font = "bold 26px system-ui, -apple-system, sans-serif"
      ctx.fillStyle = "#e0e7ff"
      ctx.fillText("Python Kurs", W / 2, H / 2 - 16)

      ctx.font = "14px system-ui, -apple-system, sans-serif"
      ctx.fillStyle = "#6366f1"
      ctx.fillText("Bereit zum Abheben …", W / 2, H / 2 + 14)

      ctx.globalAlpha = 1

      animId = requestAnimationFrame(frame)
    }

    animId = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener("resize", resize)
    }
  }, [onDone, router])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-50 w-full h-full"
      style={{ background: "#060e1c" }}
    />
  )
}
