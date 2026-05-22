"use client"

interface Props {
  errorFound: boolean
}

export default function StatusBadge({ errorFound }: Props) {
  if (errorFound) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
        <span className="w-2 h-2 rounded-full bg-red-400" />
        Fehler gefunden
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
      <span className="w-2 h-2 rounded-full bg-emerald-400" />
      Kein Fehler
    </span>
  )
}
