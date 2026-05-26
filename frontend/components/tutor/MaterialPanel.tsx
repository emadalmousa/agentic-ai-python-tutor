"use client"

import { useState } from "react"
import type { UploadResponse } from "@/types/tutor"

interface Props {
  dark: boolean
  uploading: boolean
  result: UploadResponse | null
  error: string | null
  fileName: string | null
  inputRef: React.RefObject<HTMLInputElement | null>
  onDrop: (file: File) => void
  onOpenPicker: () => void
  onFileInput: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export default function MaterialPanel({
  dark,
  uploading,
  result,
  error,
  fileName,
  inputRef,
  onDrop,
  onOpenPicker,
  onFileInput,
}: Props) {
  const [dragOver, setDragOver] = useState(false)

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type === "application/pdf") {
      onDrop(file)
    }
  }

  // Determine visual state
  const isSuccess = result && !error
  const isError = !!error

  let borderColor: string
  let bgColor: string
  let glowStyle: string

  if (isError) {
    borderColor = "border-red-500/40"
    bgColor = dark ? "bg-red-500/5" : "bg-red-50"
    glowStyle = ""
  } else if (isSuccess) {
    borderColor = "border-emerald-500/40"
    bgColor = dark ? "bg-emerald-500/5" : "bg-emerald-50"
    glowStyle = ""
  } else if (dragOver) {
    borderColor = "border-amber-400"
    bgColor = dark ? "bg-amber-500/10" : "bg-amber-50"
    glowStyle = "shadow-[0_0_24px_rgba(245,158,11,0.15)]"
  } else {
    borderColor = "border-amber-500/40"
    bgColor = dark ? "bg-[#0d1b2a]" : "bg-white"
    glowStyle = ""
  }

  return (
    <div className="h-full overflow-y-auto px-4 py-4">
      <div
        role="button"
        tabIndex={0}
        onClick={onOpenPicker}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onOpenPicker() }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={[
          "relative flex flex-col items-center justify-center gap-4",
          "min-h-[280px] cursor-pointer select-none",
          "rounded-2xl border-2 border-dashed",
          "transition-all duration-200",
          borderColor,
          bgColor,
          glowStyle,
        ].join(" ")}
      >
        {/* Loading overlay */}
        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/20 backdrop-blur-sm z-10">
            <div className="flex flex-col items-center gap-3">
              <svg
                className="animate-spin h-8 w-8 text-amber-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-700"}`}>
                Wird hochgeladen...
              </span>
            </div>
          </div>
        )}

        {/* Success state */}
        {isSuccess && !uploading && (
          <div className="flex flex-col items-center gap-3 py-4">
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/30">
              <svg className="w-7 h-7 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="text-center">
              <p className={`text-sm font-semibold ${dark ? "text-emerald-300" : "text-emerald-700"}`}>
                {fileName}
              </p>
              <p className={`text-xs mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                {result.chunks} Abschnitte verarbeitet
              </p>
            </div>
            <p className={`text-xs mt-2 ${dark ? "text-gray-500" : "text-gray-400"}`}>
              Klicke erneut, um ein anderes PDF hochzuladen.
            </p>
          </div>
        )}

        {/* Error state */}
        {isError && !uploading && (
          <div className="flex flex-col items-center gap-3 py-4">
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-red-500/10 border border-red-500/30">
              <svg className="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="text-center">
              <p className={`text-sm font-semibold ${dark ? "text-red-300" : "text-red-700"}`}>
                Upload fehlgeschlagen
              </p>
              <p className={`text-xs mt-1 max-w-[300px] ${dark ? "text-red-400/80" : "text-red-500"}`}>
                {error}
              </p>
            </div>
            <p className={`text-xs mt-2 ${dark ? "text-gray-500" : "text-gray-400"}`}>
              Klicke erneut, um es nochmal zu versuchen.
            </p>
          </div>
        )}

        {/* Default idle state */}
        {!isSuccess && !isError && !uploading && (
          <div className="flex flex-col items-center gap-3 py-4">
            <span className="text-5xl">📖</span>
            <div className="text-center">
              <p className={`text-sm font-semibold ${dark ? "text-amber-300" : "text-amber-700"}`}>
                PDF-Lernmaterial hochladen
              </p>
              <p className={`text-xs mt-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                Klicke hier oder ziehe eine PDF-Datei in diesen Bereich
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Explanation text */}
      <p className={`text-center text-xs mt-4 ${dark ? "text-gray-500" : "text-gray-400"}`}>
        Das Lernmaterial wird bei jeder Code-Analyse als Kontext genutzt.
      </p>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={onFileInput}
      />
    </div>
  )
}
