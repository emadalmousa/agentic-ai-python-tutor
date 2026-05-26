"use client"

import ReactMarkdown from "react-markdown"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism"
import type { Components } from "react-markdown"

interface Props {
  content: string
  dark: boolean
  isUser?: boolean
  onInsertCode?: (code: string) => void
}

export default function MarkdownMessage({ content, dark, isUser, onInsertCode }: Props) {
  const prose = isUser
    ? "text-white text-sm leading-relaxed"
    : dark
      ? "text-gray-200 text-sm leading-relaxed"
      : "text-gray-800 text-sm leading-relaxed"

  const components: Components = {
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "")
      const isBlock = !!match
      const codeText = String(children).replace(/\n$/, "")

      if (isBlock) {
        return (
          <div className="my-2 rounded-lg overflow-hidden text-xs">
            <div className={`flex items-center justify-between px-3 py-1.5 ${dark ? "bg-[#1a1a2e]" : "bg-gray-200"}`}>
              <span className={`text-xs font-mono ${dark ? "text-indigo-400" : "text-indigo-600"}`}>
                {match[1]}
              </span>
              {onInsertCode && match[1] === "python" && (
                <button
                  onClick={() => onInsertCode(codeText)}
                  className={`text-xs px-2 py-0.5 rounded transition-colors ${
                    dark
                      ? "text-indigo-300 hover:bg-indigo-500/20 hover:text-indigo-200"
                      : "text-indigo-600 hover:bg-indigo-100"
                  }`}
                  title="Code in Editor übernehmen"
                >
                  In Editor
                </button>
              )}
            </div>
            <SyntaxHighlighter
              style={dark ? oneDark : oneLight}
              language={match[1]}
              PreTag="div"
              customStyle={{ margin: 0, borderRadius: 0, fontSize: "0.75rem" }}
            >
              {codeText}
            </SyntaxHighlighter>
          </div>
        )
      }

      return (
        <code
          className={`px-1.5 py-0.5 rounded text-xs font-mono ${
            isUser
              ? "bg-white/20 text-white"
              : dark
                ? "bg-[#1e2f45] text-indigo-300"
                : "bg-indigo-50 text-indigo-700"
          }`}
          {...props}
        >
          {children}
        </code>
      )
    },

    p({ children }) {
      return <p className="mb-2 last:mb-0">{children}</p>
    },

    ul({ children }) {
      return <ul className="mb-2 ml-4 list-disc space-y-0.5">{children}</ul>
    },

    ol({ children }) {
      return <ol className="mb-2 ml-4 list-decimal space-y-0.5">{children}</ol>
    },

    li({ children }) {
      return <li className="leading-relaxed">{children}</li>
    },

    strong({ children }) {
      return (
        <strong className={`font-semibold ${isUser ? "text-white" : dark ? "text-indigo-300" : "text-indigo-700"}`}>
          {children}
        </strong>
      )
    },

    blockquote({ children }) {
      return (
        <blockquote className={`border-l-2 pl-3 my-2 italic ${dark ? "border-indigo-500 text-gray-400" : "border-indigo-300 text-gray-500"}`}>
          {children}
        </blockquote>
      )
    },
  }

  return (
    <div className={prose}>
      <ReactMarkdown components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
