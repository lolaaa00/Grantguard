import Link from 'next/link';

export default function Home() {
  return <main className="shell">
    <nav className="nav"><Link className="brand" href="/">GrantGuard</Link><span className="pill">GenLayer Studionet · 61999</span></nav>
    <section className="hero"><div className="eyebrow">Consensus-powered grant evaluation</div><h1>Fund ideas after the evidence survives review.</h1><p>GrantGuard turns grant selection into a transparent, challengeable workflow. Sponsors freeze the rubric, applicants submit public evidence, and GenLayer validators independently evaluate every criterion before native GEN is awarded.</p><div className="actions"><Link className="button" href="/rounds">Explore grant rounds</Link><Link className="button secondary" href="/submit">Submit a proposal</Link></div></section>
    <section className="section"><div className="grid"><article className="card"><h3>Frozen criteria</h3><p className="muted">The rubric, evidence policy, deadline, and funding are committed before proposals are reviewed.</p></article><article className="card"><h3>Independent review</h3><p className="muted">Validators evaluate public proposal evidence and return structured criterion-level findings.</p></article><article className="card"><h3>Challenge before payout</h3><p className="muted">Qualified proposals enter a bonded challenge window before finalization and award.</p></article></div></section>
    <footer className="footer">Built on GenLayer Studionet · Public evidence · Fail-closed settlement</footer>
  </main>;
}
