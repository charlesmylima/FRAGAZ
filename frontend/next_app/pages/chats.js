import { useEffect, useState, useRef } from 'react'

export default function Chats() {
  // Avoid reading localStorage during server-side rendering to prevent
  // hydration mismatches. Initialize empty and populate on client.
  const [conversations, setConversations] = useState({})
  const [active, setActive] = useState(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('fragaz_conversations') || '{}')
      setConversations(saved || {})
      const keys = Object.keys(saved || {})
      if (keys.length) setActive(keys[keys.length - 1])
    } catch (e) {
      setConversations({})
    } finally {
      setMounted(true)
    }
  }, [])

  useEffect(() => {
    if (!mounted) return
    try {
      localStorage.setItem('fragaz_conversations', JSON.stringify(conversations))
    } catch (e) {
      // ignore
    }
  }, [conversations, mounted])

  // autoscroll to bottom when active conversation updates
  const messagesRef = useRef(null)
  const endRef = useRef(null)
  useEffect(() => {
    if (!active) return
    // scroll the messages container to bottom
    try {
      if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
      else if (messagesRef.current) messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    } catch (e) {
      // ignore
    }
  }, [conversations, active])

  function newConversation() {
    const id = 'conv-' + Date.now()
    const next = { ...conversations, [id]: { id, title: 'Conversação ' + Object.keys(conversations).length, messages: [] } }
    setConversations(next)
    setActive(id)
  }

  function send() {
    if (!active || !query) return
    const conv = conversations[active]
    const userMsg = { sender: 'user', text: query }
    conv.messages.push(userMsg)
    setConversations({ ...conversations, [active]: conv })
    setQuery('')
    // call local python API
    fetch('http://127.0.0.1:8765/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: userMsg.text, k: 5 }) })
      .then(r => {
        if (!r.ok) throw new Error('backend-error:' + r.status)
        return r.json()
      })
      .then(data => {
        // backend returns { answer, confidence, sources }
        const text = data.answer || ((data.sources || []).map(s => `${s.title || s.id} — ${s.source || ''}: ${ (s.content||'').slice(0,200)}`).join('\n\n'))
        const assistant = { sender: 'assistant', text }
        conv.messages.push(assistant)
        setConversations({ ...conversations, [active]: conv })
        setResults(data.sources || [])
      })
      .catch(err => {
        const msg = err.message && err.message.startsWith('backend-error') ? 'Erro no backend (status). Verifique se o Python local API está rodando.' : 'Erro ao conectar ao backend: ' + err.message
        const assistant = { sender: 'assistant', text: msg }
        conv.messages.push(assistant)
        setConversations({ ...conversations, [active]: conv })
      })
  }

  return (
    <div className="page">
      <header className="header">
        <h1>FRAGAZ — Chat</h1>
        <nav>
          <a href="/">Painel</a>
          <a href="/chats">Chat</a>
        </nav>
      </header>

      <main className="container chat-grid">
        <aside className="side">
          <button onClick={newConversation} className="btn">Nova Conversação</button>
          {/* Render conversation list only after hydration to avoid SSR/CSR mismatch */}
          <ul className="conv-list">
            {mounted && Object.values(conversations).map(c => (
              <li key={c.id} className={c.id === active ? 'active' : ''} onClick={() => setActive(c.id)}>
                {c.title}
              </li>
            ))}
          </ul>
        </aside>

        <section className="chat-area">
          {active ? (
            <>
              <div className="messages" ref={messagesRef}>
                {(conversations[active] && conversations[active].messages || []).map((m, i) => (
                  <div key={i} className={`msg ${m.sender === 'user' ? 'msg-user' : 'msg-assistant'}`}>
                    <pre>{m.text}</pre>
                  </div>
                ))}
                <div ref={endRef} />
              </div>

              <div className="composer">
                <textarea value={query} onChange={e => setQuery(e.target.value)} placeholder="Digite sua pergunta" />
                <button onClick={send} className="btn">Enviar</button>
              </div>
            </>
          ) : (
            <div className="empty">Selecione ou crie uma conversação.</div>
          )}
        </section>
      </main>

      <footer className="footer">PoC FRAGAZ — chat</footer>
    </div>
  )
}

