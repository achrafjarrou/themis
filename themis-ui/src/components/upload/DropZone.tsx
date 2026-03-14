import { useRef, useState } from "react"

export function DropZone({ file, onFile }: { file: File|null; onFile: (f:File)=>void }) {
  const [drag, setDrag] = useState(false)
  const ref = useRef<HTMLInputElement>(null)

  const handle = (f: File|undefined) => { if (f?.type==="application/pdf") onFile(f) }

  return (
    <div
      onClick={() => ref.current?.click()}
      onDrop={e => { e.preventDefault(); setDrag(false); handle(e.dataTransfer.files[0]) }}
      onDragOver={e => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      style={{
        padding:"32px 24px", borderRadius:12, textAlign:"center", cursor:"pointer",
        border: drag ? "2px dashed #3b82f6" : file ? "2px dashed #10b981" : "2px dashed var(--border2)",
        background: drag ? "rgba(59,130,246,0.06)" : file ? "rgba(16,185,129,0.04)" : "var(--bg2)",
        transition:"all .2s",
      }}
    >
      <input ref={ref} type="file" accept=".pdf" style={{ display:"none" }}
        onChange={e => handle(e.target.files?.[0])} />

      {file ? (
        <div>
          <div style={{ fontSize:28, marginBottom:8 }}>✅</div>
          <div style={{ fontFamily:"var(--display)", fontWeight:700, color:"#10b981", fontSize:14, marginBottom:4 }}>{file.name}</div>
          <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"#34d39988" }}>
            {(file.size/1024/1024).toFixed(2)} MB · Ready to analyze
          </div>
        </div>
      ) : (
        <div>
          <div style={{ fontSize:32, marginBottom:10 }}>📄</div>
          <div style={{ fontFamily:"var(--display)", fontWeight:600, color:"#e2e8f0", fontSize:14, marginBottom:4 }}>
            {drag ? "Drop it here" : "Drop PDF or click to browse"}
          </div>
          <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text3)" }}>PDF only · Max 10 MB</div>
        </div>
      )}
    </div>
  )
}