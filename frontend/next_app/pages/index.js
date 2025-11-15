import Head from 'next/head'
import DocList from '../components/DocList'

export default function Home({ docs }) {
  return (
    <div className="page">
      <Head>
        <title>FRAGAZ — Painel</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <header className="header">
        <h1>FRAGAZ — Painel</h1>
        <nav>
          <a href="/">Painel</a>
          <a href="/chats">Chat</a>
        </nav>
      </header>

      <main className="container">
        <section>
          <h2>Últimos documentos</h2>
          <DocList docs={docs} />
        </section>
      </main>

      <footer className="footer">PoC FRAGAZ — painel de documentos</footer>
    </div>
  )
}

export async function getServerSideProps() {
  const fs = require('fs')
  const path = require('path')
  // Try to locate .fragaz_index.json by searching upward from cwd (next dev runs in frontend/next_app)
  function findIndexFile(startDir, maxUp = 4) {
    let dir = startDir
    for (let i = 0; i < maxUp; i++) {
      const candidate = path.join(dir, '.fragaz_index.json')
      if (fs.existsSync(candidate)) return candidate
      dir = path.resolve(dir, '..')
    }
    return null
  }

  const indexPath = findIndexFile(process.cwd(), 5)
  let docs = []
  if (indexPath) {
    try {
      const raw = fs.readFileSync(indexPath, 'utf-8')
      docs = JSON.parse(raw)
      // show most recent first
      docs = docs.slice().reverse().slice(0, 50)
    } catch (e) {
      docs = []
    }
  } else {
    docs = []
  }
  return { props: { docs } }
}
