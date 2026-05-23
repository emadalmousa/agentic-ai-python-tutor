"use client"

interface Props {
  dark: boolean
  onToggleDark: () => void
}

export default function Header({ dark, onToggleDark }: Props) {
  return (
    <header
      className={`sticky top-0 z-50 flex items-center justify-between px-6 py-3 border-b flex-shrink-0 ${
        dark
          ? "bg-[#080f1e]/95 border-[#1e2f45] backdrop-blur-sm"
          : "bg-white/95 border-gray-200 backdrop-blur-sm"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="text-lg">🤖</span>
        <div>
          <span className={`font-bold text-sm ${dark ? "text-white" : "text-gray-900"}`}>
            Python Tutor
          </span>
          <span className={`ml-2 text-xs ${dark ? "text-gray-500" : "text-gray-400"}`}>
            Agentic AI
          </span>
        </div>
      </div>

      <button
        onClick={onToggleDark}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
          dark
            ? "border-[#2d3f55] text-gray-400 hover:bg-[#1e2f45] hover:text-gray-200"
            : "border-gray-200 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        }`}
      >
        {dark ? (
          <>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            Hell
          </>
        ) : (
          <>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            Dunkel
          </>
        )}
      </button>
    </header>
  )
}
