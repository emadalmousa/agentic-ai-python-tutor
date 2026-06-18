"use client"

import type { ChatHistoryItem } from "@/types/tutor"
import { useTheme } from "@/context/ThemeContext"

interface Props {
  items: ChatHistoryItem[]
  activeId: number | null
  onNewChat: () => void
  onSelect: (item: ChatHistoryItem) => void
  loading: boolean
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86_400_000)
  if (diffDays === 0) return "Heute"
  if (diffDays === 1) return "Gestern"
  if (diffDays < 7) return `vor ${diffDays} Tagen`
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" })
}

export default function ChatSidebar({ items, activeId, onNewChat, onSelect, loading }: Props) {
  const { dark } = useTheme()

  const bg     = dark ? "bg-[#0a1628] border-[#1e2f45]" : "bg-white border-gray-200"
  const subCol = dark ? "text-gray-500" : "text-gray-400"
  const textCol = dark ? "text-gray-300" : "text-gray-700"

  return (
    <div className={`flex flex-col h-full border-r ${bg}`} style={{ width: 220 }}>

      {/* New chat button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 active:scale-[0.98] text-white transition-all"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Neuer Chat
        </button>
      </div>

      {/* History label */}
      <div className={`px-3 pb-1 text-xs font-semibold uppercase tracking-wider ${subCol}`}>
        Verlauf
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
        {loading && (
          <div className={`text-xs text-center py-6 animate-pulse ${subCol}`}>Lädt…</div>
        )}
        {!loading && items.length === 0 && (
          <div className={`text-xs text-center py-6 ${subCol}`}>Noch keine Chats</div>
        )}
        {items.map((item) => {
          const active = item.id === activeId
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item)}
              className={`w-full text-left px-3 py-2.5 rounded-xl transition-all group ${
                active
                  ? dark ? "bg-indigo-600/20 border border-indigo-500/30" : "bg-indigo-50 border border-indigo-200"
                  : dark ? "hover:bg-[#111e30] border border-transparent" : "hover:bg-gray-50 border border-transparent"
              }`}
            >
              <p className={`text-xs font-medium leading-tight truncate ${
                active ? (dark ? "text-indigo-300" : "text-indigo-700") : textCol
              }`}>
                {item.title}
              </p>
              <p className={`text-xs mt-0.5 ${subCol}`}>
                {formatDate(item.created_at)} · {item.message_count} Nachrichten
              </p>
            </button>
          )
        })}
      </div>

    </div>
  )
}
