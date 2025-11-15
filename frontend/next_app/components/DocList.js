export default function DocList({ docs = [] }) {
  if (!docs || docs.length === 0) return <p>Nenhum documento indexado ainda.</p>
  return (
    <ul className="doc-list">
      {docs.map(d => (
        <li key={d.id} className="doc-item">
          <h3>{d.title}</h3>
          <div className="meta">Fonte: {d.source}</div>
          <p>{d.content.slice(0, 300)}{d.content.length>300? '...':''}</p>
        </li>
      ))}
    </ul>
  )
}
