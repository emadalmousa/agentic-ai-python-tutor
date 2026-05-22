"use client"

import dynamic from "next/dynamic"
import { useEffect, useState } from "react"
import "prismjs/themes/prism-tomorrow.css"

const Editor = dynamic(() => import("react-simple-code-editor"), { ssr: false })

interface Props {
  code: string
  onChange: (code: string) => void
  dark: boolean
}

export default function CodeEditor({ code, onChange, dark }: Props) {
  const [highlight, setHighlight] = useState<((code: string) => string) | null>(null)

  // Prism.js lazy laden — nur im Browser, nicht auf dem Server
  useEffect(() => {
    import("prismjs").then((Prism) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      import("prismjs/components/prism-python" as any).then(() => {
        setHighlight(() => (c: string) =>
          Prism.highlight(c, Prism.languages.python, "python")
        )
      })
    })
  }, [])

  const editorStyle = {
    fontFamily: '"Fira Code", "Fira Mono", monospace',
    fontSize: 14,
    minHeight: 160,
    outline: "none",
  }

  return (
    <div className={`rounded-xl overflow-hidden border text-sm ${dark
      ? "border-[#2d3f55] bg-[#0d1b2a]"
      : "border-gray-200 bg-gray-50"}`}>
      {highlight ? (
        <Editor
          value={code}
          onValueChange={onChange}
          highlight={highlight}
          padding={16}
          style={editorStyle}
          textareaClassName="focus:outline-none"
        />
      ) : (
        // Fallback solange Prism noch lädt
        <textarea
          value={code}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full p-4 font-mono text-sm focus:outline-none resize-none ${dark
            ? "bg-[#0d1b2a] text-gray-200"
            : "bg-gray-50 text-gray-800"}`}
          rows={8}
          placeholder="Python-Code hier eingeben..."
        />
      )}
    </div>
  )
}
