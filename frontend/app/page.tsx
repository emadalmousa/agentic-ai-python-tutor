"use client"

import { useState } from "react"
import Header from "@/components/tutor/Header"
import CodeEditor from "@/components/tutor/CodeEditor"
import EditorFooter from "@/components/tutor/EditorFooter"
import ChatPanel from "@/components/tutor/ChatPanel"
import { useChat } from "@/hooks/useChat"
import { useCodeRunner } from "@/hooks/useCodeRunner"

export default function Home() {
  const [dark, setDark] = useState(true)

  const [code, setCode] = useState("for i in range(5)\n    print(i)")
  const {
    history, input, setInput,
    loading, analyzing, uploading, materialName,
    error,
    send, analyze, reset,
    openFilePicker, handleFileInput, fileInputRef,
    bottomRef,
  } = useChat(code)
  const { output, loading: running, run } = useCodeRunner()

  const bg      = dark ? "bg-[#060e1c] text-white" : "bg-gray-100 text-gray-900"
  const border  = dark ? "border-[#1e2f45]"        : "border-gray-200"
  const labelCls = dark ? "block text-xs font-medium text-gray-400 mb-1.5" : "block text-xs font-medium text-gray-500 mb-1.5"

  return (
    <div className={`${bg} h-screen flex flex-col overflow-hidden`}>

      <Header dark={dark} onToggleDark={() => setDark(!dark)} />

      <div className="flex flex-1 min-h-0">

        {/* ════ LINKE SEITE: Code-Editor ════ */}
        <div className={`w-[480px] flex-shrink-0 flex flex-col border-r ${border}`}>
          <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
            <label className={labelCls}>Python-Code</label>
            <CodeEditor code={code} onChange={setCode} dark={dark} />
          </div>
          <EditorFooter
            dark={dark}
            code={code}
            running={running}
            analyzing={analyzing}
            output={output}
            onRun={() => run(code)}
            onAnalyze={analyze}
          />
        </div>

        {/* ════ RECHTE SEITE: Chat ════ */}
        <div className="flex-1 min-w-0">
          <ChatPanel
            history={history}
            input={input}
            loading={loading}
            analyzing={analyzing}
            uploading={uploading}
            materialName={materialName}
            error={error}
            bottomRef={bottomRef}
            fileInputRef={fileInputRef}
            onInput={setInput}
            onSend={send}
            onReset={reset}
            onOpenFilePicker={openFilePicker}
            onFileInput={handleFileInput}
            onInsertCode={setCode}
            dark={dark}
          />
        </div>

      </div>
    </div>
  )
}
