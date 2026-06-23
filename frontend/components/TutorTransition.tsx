"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"

interface Props {
  onDone: () => void
}

// Scene durations (ms)
const S1_END = 2200   // Scene 1: Robot appears, waves hello
const S2_END = 4400   // Scene 2: Robot thinks, shows code
const S3_END = 6600   // Scene 3: Robot excited, "Los geht's!" → navigate

const FADE_DUR = 350  // cross-fade between scenes

export default function TutorTransition({ onDone }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const router = useRouter()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D
    if (!ctx) return

    let animId: number
    let startTime: number | null = null
    let navigated = false

    function resize() {
      if (!canvas) return
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener("resize", resize)

    function easeOut(t: number) { return 1 - Math.pow(1 - t, 3) }
    function easeInOut(t: number) { return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2 }

    // Floating particles
    type Particle = { x: number; y: number; vx: number; vy: number; r: number; alpha: number; color: string }
    const COLORS = ["#6366f1","#8b5cf6","#60a5fa","#a78bfa","#34d399"]
    const particles: Particle[] = Array.from({ length: 55 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      r: Math.random() * 2 + 0.8,
      alpha: Math.random() * 0.35 + 0.1,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    }))

    // Floating code tokens (scene 2)
    type Token = { text: string; x: number; y: number; vy: number; alpha: number; color: string; size: number }
    const CODE_TOKENS = [
      "def learn():", "for i in range(∞):", "if curious:", "  print('Hallo!')",
      "import brain", "while True:", "  ask()", "lambda x: x**2",
      "class Tutor:", "  def __init__:", "return wisdom",
    ]
    const tokens: Token[] = CODE_TOKENS.map((text, i) => ({
      text,
      x: 80 + Math.random() * (canvas.width - 160),
      y: canvas.height + 30 + i * 25,
      vy: -(0.6 + Math.random() * 0.5),
      alpha: 0,
      color: COLORS[i % COLORS.length],
      size: 12 + Math.floor(Math.random() * 4),
    }))

    // --- Draw background ---
    function drawBg(W: number, H: number, scene: number, sceneT: number) {
      const topColor = scene === 3 ? "#1a0a2e" : "#0d1224"

      const bg = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W * 0.75)
      bg.addColorStop(0, topColor)
      bg.addColorStop(1, "#060e1c")
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, W, H)

      // Scene glow pulse
      const pulse = 0.7 + Math.sin(sceneT * 0.004) * 0.3
      const glowAlpha = 0.15 * pulse
      const glowRgb = scene === 1 ? "99,102,241" : scene === 2 ? "59,130,246" : "168,85,247"
      const g = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, 300)
      g.addColorStop(0, `rgba(${glowRgb},${glowAlpha})`)
      g.addColorStop(1, "transparent")
      ctx.fillStyle = g
      ctx.globalAlpha = pulse
      ctx.fillRect(0, 0, W, H)
      ctx.globalAlpha = 1
    }

    // --- Draw robot ---
    function drawRobot(cx: number, cy: number, scale: number, alpha: number, elapsed: number, scene: number, sceneT: number) {
      ctx.save()
      ctx.globalAlpha = alpha
      ctx.translate(cx, cy)
      ctx.scale(scale, scale)

      const bobY = Math.sin(elapsed * 0.003) * 5
      const bobX = scene === 3 ? Math.sin(elapsed * 0.008) * 8 : 0 // excited bounce in scene 3
      ctx.translate(bobX, bobY)

      // Shadow
      ctx.beginPath()
      ctx.ellipse(0, 58, 30 + Math.abs(bobX), 7, 0, 0, Math.PI * 2)
      ctx.fillStyle = "rgba(99,102,241,0.15)"
      ctx.fill()

      // Body
      const bodyGrad = ctx.createLinearGradient(-22, -10, 22, 44)
      bodyGrad.addColorStop(0, scene === 3 ? "#5b21b6" : "#3730a3")
      bodyGrad.addColorStop(1, "#1e1b4b")
      ctx.beginPath()
      ctx.roundRect(-22, -8, 44, 52, 8)
      ctx.fillStyle = bodyGrad
      ctx.fill()
      ctx.strokeStyle = scene === 3 ? "#a78bfa" : "#6366f1"
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Chest panel
      ctx.beginPath()
      ctx.roundRect(-14, 8, 28, 22, 5)
      ctx.fillStyle = "#0f172a"
      ctx.fill()
      ctx.strokeStyle = "#4f46e5"
      ctx.lineWidth = 1
      ctx.stroke()

      // Chest lights
      const lightColors = ["#34d399","#f59e0b","#6366f1"]
      for (let i = 0; i < 3; i++) {
        const pulse = 0.55 + Math.sin(elapsed * 0.005 + i * 1.2) * 0.45
        ctx.beginPath()
        ctx.arc(-8 + i * 8, 22, 3.5, 0, Math.PI * 2)
        ctx.fillStyle = lightColors[i]
        ctx.globalAlpha = alpha * pulse
        ctx.fill()
        ctx.globalAlpha = alpha
      }

      // Head
      const headGrad = ctx.createLinearGradient(-18, -54, 18, -20)
      headGrad.addColorStop(0, scene === 3 ? "#5b21b6" : "#4338ca")
      headGrad.addColorStop(1, "#312e81")
      ctx.beginPath()
      ctx.roundRect(-18, -54, 36, 36, 10)
      ctx.fillStyle = headGrad
      ctx.fill()
      ctx.strokeStyle = scene === 3 ? "#c4b5fd" : "#818cf8"
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Antenna
      ctx.beginPath()
      ctx.moveTo(0, -54)
      ctx.lineTo(0, -68)
      ctx.strokeStyle = "#a5b4fc"
      ctx.lineWidth = 2
      ctx.stroke()
      const antP = 0.5 + Math.sin(elapsed * 0.007) * 0.5
      ctx.beginPath()
      ctx.arc(0, -70, 4.5, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${scene === 3 ? "168,85,247" : "99,102,241"},${antP})`
      ctx.fill()
      ctx.beginPath()
      ctx.arc(0, -70, 2.5, 0, Math.PI * 2)
      ctx.fillStyle = "#e0e7ff"
      ctx.fill()

      // Eyes
      const blink = Math.floor(elapsed / 2500) % 2 === 0 || elapsed % 2500 < 120
      const eyeH = blink ? 7 : 1.5

      // Scene 2: thinking eyes (look up-right)
      const eyeOffX = scene === 2 ? 2 : 0
      const eyeOffY = scene === 2 ? -2 : 0

      for (let e = 0; e < 2; e++) {
        const ex = e === 0 ? -8 : 8
        ctx.beginPath()
        ctx.ellipse(ex, -37, 5, eyeH / 2, 0, 0, Math.PI * 2)
        ctx.fillStyle = "#bfdbfe"
        ctx.fill()
        if (blink) {
          ctx.beginPath()
          ctx.arc(ex + eyeOffX, -37 + eyeOffY, 2.5, 0, Math.PI * 2)
          ctx.fillStyle = "#1e40af"
          ctx.fill()
        }
      }

      // Mouth — smile (scene 1+3) or flat thinking (scene 2)
      ctx.beginPath()
      if (scene === 2) {
        ctx.moveTo(-7, -24)
        ctx.lineTo(7, -24)
        ctx.strokeStyle = "#93c5fd"
        ctx.lineWidth = 2
        ctx.stroke()
      } else {
        ctx.arc(0, -27, 7, 0.2, Math.PI - 0.2)
        ctx.strokeStyle = scene === 3 ? "#c4b5fd" : "#93c5fd"
        ctx.lineWidth = 2
        ctx.stroke()
      }

      // Left arm
      const leftRot = scene === 2 ? 10 : Math.sin(elapsed * 0.004) * 10 - 5
      ctx.save()
      ctx.translate(-22, 4)
      ctx.rotate(leftRot * Math.PI / 180)
      ctx.beginPath()
      ctx.roundRect(-5, 0, 10, 26, 5)
      ctx.fillStyle = "#3730a3"
      ctx.fill()
      ctx.strokeStyle = "#6366f1"
      ctx.lineWidth = 1
      ctx.stroke()
      ctx.restore()

      // Right arm
      // Scene 1: wave, Scene 2: hand to chin (thinking), Scene 3: thumbs up
      let rightRot = 0
      if (scene === 1) rightRot = -30 + Math.sin(elapsed * 0.007) * 28
      else if (scene === 2) rightRot = -80  // arm up to head
      else rightRot = -50 + Math.sin(sceneT * 0.01) * 10

      ctx.save()
      ctx.translate(22, 4)
      ctx.rotate(rightRot * Math.PI / 180)
      ctx.beginPath()
      ctx.roundRect(-5, 0, 10, 26, 5)
      ctx.fillStyle = "#3730a3"
      ctx.fill()
      ctx.strokeStyle = "#6366f1"
      ctx.lineWidth = 1
      ctx.stroke()

      // Thumbs up in scene 3
      if (scene === 3) {
        ctx.beginPath()
        ctx.roundRect(-4, -10, 8, 12, 4)
        ctx.fillStyle = "#4338ca"
        ctx.fill()
        ctx.strokeStyle = "#818cf8"
        ctx.lineWidth = 1
        ctx.stroke()
      }
      ctx.restore()

      // Legs
      for (let leg = 0; leg < 2; leg++) {
        const legX = leg === 0 ? -10 : 10
        const legSway = scene === 3
          ? Math.sin(elapsed * 0.008 + leg * Math.PI) * 12
          : Math.sin(elapsed * 0.003 + leg * Math.PI) * 4
        ctx.save()
        ctx.translate(legX, 44)
        ctx.rotate(legSway * Math.PI / 180)
        ctx.beginPath()
        ctx.roundRect(-6, 0, 12, 20, 4)
        ctx.fillStyle = "#1e1b4b"
        ctx.fill()
        ctx.strokeStyle = "#4f46e5"
        ctx.lineWidth = 1
        ctx.stroke()
        ctx.beginPath()
        ctx.roundRect(-8, 18, 16, 8, 3)
        ctx.fillStyle = "#312e81"
        ctx.fill()
        ctx.restore()
      }

      // Scene 2: thinking dots above head
      if (scene === 2) {
        const dotAlpha = Math.min(sceneT / 400, 1)
        ctx.globalAlpha = alpha * dotAlpha
        for (let d = 0; d < 3; d++) {
          const bounce = Math.sin(elapsed * 0.006 + d * 1.1) * 3
          ctx.beginPath()
          ctx.arc(25 + d * 10, -65 + bounce, 3.5, 0, Math.PI * 2)
          ctx.fillStyle = "#818cf8"
          ctx.fill()
        }
        ctx.globalAlpha = alpha
      }

      // Scene 3: sparkles around robot
      if (scene === 3) {
        const sparkCount = 6
        for (let s = 0; s < sparkCount; s++) {
          const angle = (s / sparkCount) * Math.PI * 2 + elapsed * 0.003
          const dist = 55 + Math.sin(elapsed * 0.005 + s) * 10
          const sx = Math.cos(angle) * dist
          const sy = Math.sin(angle) * dist - 10
          const sp = 0.5 + Math.sin(elapsed * 0.007 + s * 1.3) * 0.5
          ctx.globalAlpha = alpha * sp * 0.8
          ctx.beginPath()
          ctx.arc(sx, sy, 3, 0, Math.PI * 2)
          ctx.fillStyle = COLORS[s % COLORS.length]
          ctx.fill()
        }
        ctx.globalAlpha = alpha
      }

      ctx.restore()
    }

    // --- Speech bubble ---
    function drawBubble(cx: number, cy: number, alpha: number, scale: number, scene: number) {
      if (alpha <= 0) return
      const lines: string[] = scene === 1
        ? ["Hallo! 👋", "Ich bin dein KI-Tutor!"]
        : scene === 2
        ? ["Lass mich", "kurz nachdenken… 🤔"]
        : ["Bereit?", "Los geht's! 🚀"]

      const bubbleColor = scene === 3 ? "#2e1065" : "#1e2f45"
      const borderColor = scene === 3 ? "#a78bfa" : "#6366f1"

      ctx.save()
      ctx.globalAlpha = alpha
      ctx.translate(cx + 50 * scale, cy - 90 * scale)
      ctx.scale(scale, scale)

      const bw = 128, bh = 56, br = 12
      ctx.beginPath()
      ctx.roundRect(0, 0, bw, bh, br)
      ctx.fillStyle = bubbleColor
      ctx.fill()
      ctx.strokeStyle = borderColor
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Tail
      ctx.beginPath()
      ctx.moveTo(10, bh)
      ctx.lineTo(-5, bh + 12)
      ctx.lineTo(24, bh)
      ctx.fillStyle = bubbleColor
      ctx.fill()
      ctx.strokeStyle = borderColor
      ctx.lineWidth = 1.5
      ctx.moveTo(10, bh); ctx.lineTo(-5, bh + 12); ctx.stroke()
      ctx.moveTo(-5, bh + 12); ctx.lineTo(24, bh); ctx.stroke()

      ctx.fillStyle = "#e0e7ff"
      ctx.font = "bold 12px system-ui, sans-serif"
      ctx.textAlign = "center"
      lines.forEach((line, i) => ctx.fillText(line, bw / 2, 21 + i * 18))
      ctx.restore()
    }

    // --- Scene label ---
    function drawSceneLabel(W: number, H: number, scene: number, alpha: number) {
      const labels = ["", "Scene 1 — Hallo!", "Scene 2 — Ich denke nach…", "Scene 3 — Bereit!"]
      const label = labels[scene] ?? ""
      if (!label || alpha <= 0) return
      ctx.save()
      ctx.globalAlpha = alpha * 0.45
      ctx.font = "11px system-ui, sans-serif"
      ctx.textAlign = "center"
      ctx.fillStyle = "#818cf8"
      ctx.fillText(label, W / 2, H - 28)
      ctx.restore()
    }

    // --- Scene dots indicator ---
    function drawDots(W: number, H: number, scene: number, alpha: number) {
      for (let i = 0; i < 3; i++) {
        const active = i + 1 === scene
        ctx.save()
        ctx.globalAlpha = alpha * (active ? 1 : 0.35)
        ctx.beginPath()
        ctx.arc(W / 2 - 16 + i * 16, H - 48, active ? 5 : 3.5, 0, Math.PI * 2)
        ctx.fillStyle = active ? "#818cf8" : "#4f46e5"
        ctx.fill()
        ctx.restore()
      }
    }

    function frame(ts: number) {
      if (!startTime) startTime = ts
      const elapsed = ts - startTime
      const W = canvas!.width, H = canvas!.height
      const cx = W / 2, cy = H / 2

      // Determine scene and local scene time
      let scene = 1
      let sceneStart = 0
      if (elapsed >= S2_END) { scene = 3; sceneStart = S2_END }
      else if (elapsed >= S1_END) { scene = 2; sceneStart = S1_END }
      const sceneT = elapsed - sceneStart

      // Cross-fade alpha (fade in new scene over FADE_DUR ms)
      const fadeAlpha = Math.min(sceneT / FADE_DUR, 1)

      ctx.clearRect(0, 0, W, H)

      // Background + particles
      drawBg(W, H, scene, sceneT)
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.alpha
        ctx.fill()
      }
      ctx.globalAlpha = 1

      // Scene 2: floating code tokens
      if (scene === 2) {
        ctx.save()
        for (const tok of tokens) {
          tok.y += tok.vy
          tok.alpha = Math.min(tok.alpha + 0.008, 0.45)
          if (tok.y < -20) { tok.y = H + 10; tok.alpha = 0 }
          ctx.globalAlpha = tok.alpha * fadeAlpha
          ctx.font = `${tok.size}px 'Fira Code', 'Courier New', monospace`
          ctx.fillStyle = tok.color
          ctx.textAlign = "left"
          ctx.fillText(tok.text, tok.x, tok.y)
        }
        ctx.restore()
      }

      // Robot appearance
      const robotAppear = elapsed < 600 ? easeOut(elapsed / 600) : 1
      const scale = 1.0 + (scene === 3 ? Math.sin(sceneT * 0.008) * 0.04 : 0)

      // Glow
      const glowGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 180)
      const glowCol = scene === 3 ? "168,85,247" : "99,102,241"
      glowGrad.addColorStop(0, `rgba(${glowCol},${0.18 * robotAppear})`)
      glowGrad.addColorStop(1, "transparent")
      ctx.fillStyle = glowGrad
      ctx.fillRect(0, 0, W, H)

      drawBubble(cx, cy, robotAppear * Math.min(sceneT / 400, 1), scale, scene)
      drawRobot(cx, cy, scale, robotAppear, elapsed, scene, sceneT)
      drawDots(W, H, scene, robotAppear)
      drawSceneLabel(W, H, scene, robotAppear)

      // Navigate after scene 3 ends — fade canvas to black, then switch
      if (elapsed >= S3_END) {
        if (!navigated) {
          navigated = true
          router.push("/tutor")
        }
        const fadeT = Math.min((elapsed - S3_END) / 500, 1)
        ctx.fillStyle = `rgba(6,14,28,${fadeT})`
        ctx.fillRect(0, 0, W, H)
        if (fadeT >= 1) {
          onDone()
          return
        }
      }

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
