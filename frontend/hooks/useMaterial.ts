"use client"

import { useState, useRef } from "react"
import { uploadMaterial } from "@/lib/api"
import type { UploadResponse } from "@/types/tutor"

export function useMaterial() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function upload(file: File) {
    setUploading(true)
    setError(null)
    setFileName(file.name)
    try {
      const data = await uploadMaterial(file)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen.")
      setResult(null)
    } finally {
      setUploading(false)
    }
  }

  function openFilePicker() {
    inputRef.current?.click()
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) upload(file)
    e.target.value = ""
  }

  return { uploading, result, error, fileName, inputRef, upload, openFilePicker, handleFileInput }
}
