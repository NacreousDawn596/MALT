import { useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent, ReactNode } from 'react';
import { compatibility, docs, downloads, examples, pipeline, RAW_DOC, RELEASE_DL, RELEASES, REPO, VERSION } from './data';

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true as const };
  const paths: Record<string, ReactNode> = {
    arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
    external: <><path d="M14 4h6v6"/><path d="M10 14 20 4"/><path d="M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6"/></>,
    copy: <><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    menu: <><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/></>,
    close: <><path d="m6 6 12 12"/><path d="M18 6 6 18"/></>,
    github: <><path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.9a3.4 3.4 0 0 0-.9-2.7c3-.3 6.1-1.5 6.1-6.7A5.2 5.2 0 0 0 18.8 4a4.8 4.8 0 0 0-.1-3S17.5.7 15 2.5a13.4 13.4 0 0 0-7 0C5.5.7 4.3 1 4.3 1A4.8 4.8 0 0 0 4.2 4 5.2 5.2 0 0 0 2.8 7.7c0 5.2 3.1 6.4 6.1 6.7A3.4 3.4 0 0 0 8 17.1V21"/></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/></>,
    mail: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></>,
    terminal: <><path d="m4 7 5 5-5 5"/><path d="M12 17h8"/></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22z"/><path d="M4 5.5v14A2.5 2.5 0 0 1 6.5 17H20"/></>,
  };
  return <svg {...common}>{paths[name] ?? paths.arrow}</svg>;
}

function CopyButton({ value, label = 'Copy' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }
  return <button className="copy-button" type="button" onClick={copy} aria-label={copied ? 'Copied' : label}>
    <Icon name={copied ? 'check' : 'copy'} size={14} /> <span>{copied ? 'Copied' : label}</span>
  </button>;
}

function WaveArt() {
  return <div className="wave-art" aria-label="Abstract mathematical ribbon in MALT's gradient palette" role="img">
    <svg className="wave-svg" viewBox="0 0 680 560" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="ribbon" x1="92" y1="410" x2="596" y2="100" gradientUnits="userSpaceOnUse"><stop stopColor="#7D75F7"/><stop offset=".28" stopColor="#B477EC"/><stop offset=".57" stopColor="#E48BD6"/><stop offset=".8" stopColor="#F4B6B2"/><stop offset="1" stopColor="#F8D98D"/></linearGradient>
        <linearGradient id="ribbonShade" x1="210" y1="450" x2="530" y2="120" gradientUnits="userSpaceOnUse"><stop stopColor="#6258D7" stopOpacity=".04"/><stop offset=".48" stopColor="#3D2D90" stopOpacity=".28"/><stop offset="1" stopColor="#fff" stopOpacity=".45"/></linearGradient>
        <filter id="softGlow" x="10" y="10" width="660" height="530" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="18"/></filter>
      </defs>
      <g opacity=".46" stroke="#A99AE8" strokeWidth=".8"><path d="M34 92H642M34 168H642M34 244H642M34 320H642M34 396H642M34 472H642"/><path d="M94 40V520M190 40V520M286 40V520M382 40V520M478 40V520M574 40V520"/></g>
      <g opacity=".65" stroke="#B3A8D9" strokeWidth="1"><path d="M45 430 632 430"/><path d="M80 480 80 76"/><path d="m626 424 6 6-6 6"/><path d="m74 82 6-6 6 6"/></g>
      <path d="M68 355C143 329 135 167 236 194c82 22 73 203 164 183 88-20 84-222 174-239 62-12 78 86 86 178" stroke="#D89AE9" strokeWidth="58" strokeLinecap="round" opacity=".3" filter="url(#softGlow)"/>
      <path d="M60 367C143 341 142 174 238 198c78 20 79 196 160 180 91-18 87-213 175-236 63-16 82 74 95 168" stroke="url(#ribbon)" strokeWidth="76" strokeLinecap="round"/>
      <path d="M60 367C143 341 142 174 238 198c78 20 79 196 160 180 91-18 87-213 175-236 63-16 82 74 95 168" stroke="url(#ribbonShade)" strokeWidth="75" strokeLinecap="round"/>
      <path d="M60 367C143 341 142 174 238 198c78 20 79 196 160 180 91-18 87-213 175-236 63-16 82 74 95 168" stroke="white" strokeOpacity=".52" strokeWidth="1.5" strokeLinecap="round"/>
      <g fill="#8C81E6"><circle cx="60" cy="367" r="4"/><circle cx="238" cy="198" r="4"/><circle cx="398" cy="378" r="4"/><circle cx="573" cy="142" r="4"/></g>
      <g fill="#8C81E6" fontFamily="monospace" fontSize="11" opacity=".8"><text x="38" y="452">x₁</text><text x="612" y="452">x₂</text><text x="48" y="65">f(x)</text><text x="531" y="500">MALT / 0.4</text></g>
    </svg>
    <div className="art-stamp"><span className="stamp-dot"/> MATHEMATICS, MADE TANGIBLE <span>01 / 03</span></div>
    <div className="art-note"><span>f(x) = sin(x) · e<sup>−0.2x</sup></span><small>PARAMETRIC STUDY</small></div>
  </div>;
}

function PlotPreview() {
  const path = useMemo(() => Array.from({ length: 160 }, (_, i) => {
    const x = (i / 159) * Math.PI * 2;
    const y = Math.sin(x);
    const px = 28 + (i / 159) * 544;
    const py = 112 - y * 72;
    return `${i === 0 ? 'M' : 'L'}${px.toFixed(2)},${py.toFixed(2)}`;
  }).join(' '), []);
  const area = `${path} L572,112 L28,112 Z`;
  return <svg className="plot-preview" viewBox="0 0 600 224" role="img" aria-label="Sine curve from zero to two pi">
    <defs><linearGradient id="plotFill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#9A83EA" stopOpacity=".22"/><stop offset="1" stopColor="#9A83EA" stopOpacity="0"/></linearGradient></defs>
    {[40,76,112,148,184].map(y => <line key={y} x1="28" x2="572" y1={y} y2={y} stroke="#e5e0ec" strokeWidth="1"/>)}
    {[28,164,300,436,572].map((x,i)=><g key={x}><line x1={x} x2={x} y1="24" y2="184" stroke="#ede9f1"/><text x={x} y="207" fill="#958da0" fontSize="10" textAnchor="middle" fontFamily="monospace">{['0','π/2','π','3π/2','2π'][i]}</text></g>)}
    <path d={area} fill="url(#plotFill)"/><path d={path} stroke="#8d79dc" strokeWidth="3" strokeLinecap="round" fill="none"/>
  </svg>;
}

function CodeWorkbench() {
  const [selected, setSelected] = useState(examples[0].id);
  const example = examples.find(item => item.id === selected)!;
  return <section className="section workbench-section" id="try-it">
    <div className="section-head split-head"><div><p className="eyebrow">A FEEL FOR THE LANGUAGE</p><h2>Small programs.<br/><em>Real semantics.</em></h2></div><p className="section-intro">A few lines can say a lot. Explore familiar MATLAB-like syntax and the behavior MALT is designed to preserve.</p></div>
    <div className="workbench">
      <div className="workbench-top"><div className="window-controls"><i/><i/><i/></div><div className="workbench-title">untitled.m <span>·</span> preview</div><div className="workbench-status"><b/> EXAMPLE PREVIEW</div></div>
      <div className="workbench-tabs" role="tablist" aria-label="Choose a code example">{examples.map(item=><button key={item.id} role="tab" aria-selected={selected===item.id} className={selected===item.id?'active':''} onClick={()=>setSelected(item.id)}>{item.label}</button>)}</div>
      <div className="workbench-body">
        <div className="code-pane"><div className="pane-label"><span>{example.eyebrow}</span><CopyButton value={example.code} label="Copy code"/></div><pre className="code-block"><code>{example.code.split('\n').map((line,i)=><span className="code-line" key={`${selected}-${i}`}><span className="line-no">{String(i+1).padStart(2,'0')}</span><span className="code-text">{line.split(/(\b(?:for|end|disp|plot|title|grid|sin|linspace)\b|\b\d+(?:\.\d+)?\b|'[^']*')/g).map((part,j)=>{
          const cls = /^(for|end)$/.test(part)?'syntax-keyword':/^(disp|plot|title|grid|sin|linspace)$/.test(part)?'syntax-function':/^\d/.test(part)?'syntax-number':/^'/.test(part)?'syntax-string':'';
          return <span className={cls} key={j}>{part}</span>;
        })}</span></span>)}</code></pre><div className="code-foot"><span>MATLAB-LIKE SOURCE</span><span>UTF-8 <b>•</b> LF</span></div></div>
        <div className="result-pane"><div className="pane-label"><span>{example.kind==='plot'?'VISUAL PREVIEW':'EXPECTED OUTPUT'}</span><span className="result-live"><i/> READY</span></div>
          <div className="result-content">{example.kind==='plot'?<PlotPreview/>:<pre className="output-block">{example.output}</pre>}<p>{example.description}</p></div>
          <div className="result-foot"><span>ILLUSTRATIVE RESULT · NOT LIVE EXECUTION</span><span>↗</span></div>
        </div>
      </div>
    </div>
    <p className="workbench-caption">The examples are shown as verified language illustrations. MALT itself runs natively through its CLI, REPL, or notebook GUI.</p>
  </section>;
}

function Architecture() {
  const [active, setActive] = useState(2);
  return <section className="section architecture-section" id="architecture">
    <div className="section-head"><p className="eyebrow">UNDER THE SURFACE</p><h2>Not a translator.<br/><em>A compiler pipeline.</em></h2><p className="section-intro">MALT gives MATLAB-like source a proper journey: structured syntax, semantic checks, readable code generation, and execution inside CPython.</p></div>
    <div className="architecture-layout">
      <div className="pipeline-list" role="tablist" aria-label="Compiler pipeline stages">{pipeline.map((item,i)=><button key={item.name} className={`pipeline-step ${active===i?'selected':''}`} onClick={()=>setActive(i)} role="tab" aria-selected={active===i}><span className="pipeline-index">0{i+1}</span><span className="pipeline-name">{item.name}</span><span className="pipeline-tag">{item.tag}</span><span className="pipeline-chevron">↗</span></button>)}</div>
      <div className="pipeline-detail" role="tabpanel"><div className="pipeline-detail-top"><span>COMPILATION STAGE</span><span>0{active+1} / 0{pipeline.length}</span></div><div className="pipeline-orb"><div className="orb-ring ring-a"/><div className="orb-ring ring-b"/><div className="orb-core">{active===0?'.m':active===1?'{}':active===2?'AST':active===3?'✓':active===4?'Py':active===5?'CP':<span>∑</span>}</div></div><p className="detail-kicker">{pipeline[active].tag}</p><h3>{pipeline[active].name}</h3><p className="detail-copy">{pipeline[active].detail}</p><div className="detail-nav"><button onClick={()=>setActive(Math.max(0,active-1))} disabled={active===0}>← Previous</button><button onClick={()=>setActive(Math.min(pipeline.length-1,active+1))} disabled={active===pipeline.length-1}>Next stage <Icon name="arrow" size={14}/></button></div></div>
    </div>
    <div className="optimization-band"><div><p className="eyebrow">THREE WAYS TO EXECUTE</p><h3>Optimization is explicit.<br/><em>Semantics stay in view.</em></h3></div><div className="optimization-levels"><div><span>00</span><b>Reference</b><p>1×1 array scalars. The slow, always-correct baseline.</p></div><div><span>01</span><b>Scalar fast paths</b><p>Native Python scalar intermediates and optimized operators.</p></div><div><span>02</span><b>Loop specialization</b><p>Conservative JIT-style lowering for eligible accumulator loops, with fallback.</p></div></div></div>
  </section>;
}

function Documentation() {
  const [query,setQuery]=useState('');
  const searchRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        document.getElementById('documentation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        searchRef.current?.focus();
      }
      if (event.key === 'Escape' && document.activeElement === searchRef.current) {
        setQuery('');
        searchRef.current?.blur();
      }
    }
    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);
  const filtered=useMemo(()=>docs.filter(d=>`${d.title} ${d.group} ${d.description} ${d.tags}`.toLowerCase().includes(query.toLowerCase().trim())),[query]);
  const groups=Array.from(new Set(filtered.map(d=>d.group)));
  return <section className="section documentation-section" id="documentation">
    <div className="section-head split-head"><div><p className="eyebrow">THE REFERENCE SHELF</p><h2>Made to be<br/><em>understood.</em></h2></div><p className="section-intro">The implementation is documented from the language rules down to the runtime API. Start with the overview, or go straight to the details.</p></div>
    <div className="docs-search"><Icon name="search" size={18}/><input ref={searchRef} value={query} onChange={(e: ChangeEvent<HTMLInputElement>)=>setQuery(e.target.value)} placeholder="Search the documentation…" aria-label="Search documentation"/><kbd>⌘ K&nbsp; · &nbsp;Ctrl K</kbd>{query&&<button onClick={()=>setQuery('')} aria-label="Clear search">×</button>}</div>
    <div className="docs-groups">{groups.length?groups.map(group=><div className="docs-group" key={group}><h3>{group}</h3><div className="docs-items">{filtered.filter(d=>d.group===group).map(d=><a className="doc-item" key={d.path} href={`${RAW_DOC}${d.path}`} target="_blank" rel="noreferrer"><div><strong>{d.title}</strong><p>{d.description}</p></div><span className="doc-path">{d.path}</span><span className="doc-arrow"><Icon name="external" size={15}/></span></a>)}</div></div>):<p className="empty-state">No documents match “{query}”. Try a different term.</p>}</div>
    <a className="text-link" href={`${REPO}/tree/master/docs`} target="_blank" rel="noreferrer">Explore all documentation <Icon name="arrow" size={15}/></a>
  </section>;
}

function Compatibility() {
  const [filter,setFilter]=useState('All');
  const states=['All','Implemented','Partial','Unsupported','Different'];
  const rows=compatibility.filter(x=>filter==='All'||x.status===filter);
  return <section className="section compatibility-section" id="compatibility">
    <div className="section-head split-head"><div><p className="eyebrow">COMPATIBILITY, WITHOUT THE ASTERISKS</p><h2>A defined subset.<br/><em>Clearly documented.</em></h2></div><p className="section-intro">MALT does not claim to be all of MATLAB. Its supported surface is documented, tested, and explicit about the boundaries.</p></div>
    <div className="compat-top"><div className="status-legend"><span><i className="status-dot implemented"/> Implemented</span><span><i className="status-dot partial"/> Partial</span><span><i className="status-dot unsupported"/> Unsupported</span><span><i className="status-dot different"/> Different</span></div><div className="compat-filters" aria-label="Filter compatibility features">{states.map(s=><button key={s} className={filter===s?'active':''} onClick={()=>setFilter(s)}>{s}</button>)}</div></div>
    <div className="compat-table-wrap"><table className="compat-table"><thead><tr><th>FEATURE</th><th>AREA</th><th>STATUS</th><th>NOTES</th><th/></tr></thead><tbody>{rows.map(row=><tr key={row.name}><td className="feature-name">{row.name}</td><td>{row.group}</td><td><span className={`status-pill ${row.status.toLowerCase()}`}>{row.status}</span></td><td className="feature-note">{row.note}</td><td><a href={`${RAW_DOC}${row.doc}`} target="_blank" rel="noreferrer" aria-label={`Read more about ${row.name}`}><Icon name="external" size={14}/></a></td></tr>)}</tbody></table></div>
    <div className="compat-note"><span>THE FULL CONTRACT</span><p>This is a curated overview. The complete compatibility matrix includes lexical syntax, operators, arrays, functions, numerical routines, graphics, I/O, errors, and intentional differences.</p><a href={`${RAW_DOC}docs/compatibility-matrix.md`} target="_blank" rel="noreferrer">Read the full matrix <Icon name="arrow" size={14}/></a></div>
  </section>;
}

function Installation() {
  const [platform,setPlatform]=useState('nix');
  const tabs=[{id:'nix',label:'Nix / NixOS'},{id:'debian',label:'Debian / Ubuntu'},{id:'windows',label:'Windows'},{id:'portable',label:'Portable Linux'}];
  const commands:Record<string,string>={
    nix:'nix run github:NacreousDawn596/MALT -- --version\n\nnix profile install github:NacreousDawn596/MALT\nmalt --version',
    debian:`sudo apt install ./malt_${VERSION}_amd64.deb\nmalt --version\nmalt repl`,
    windows:'malt --version\nmalt eval "2 + 2"\nmalt repl\nmalt gui',
    portable:'tar -xzf malt-linux-portable-amd64.tar.gz\n./dist/malt/malt --version\n./dist/malt/malt repl',
  };
  const details:Record<string,{title:string;body:string;label:string;meta:string}>={
    nix:{title:'Native, reproducible by design.',body:'MALT is packaged as a Nix flake. Run it directly, install it into your profile, or add the package to a NixOS system configuration. No PyInstaller bundle, no mutable application files in the store.',label:'RUN WITH NIX',meta:'x86_64-linux · native flake'},
    debian:{title:'A familiar package-manager install.',body:'The Debian package installs MALT under /opt and exposes the malt command. NumPy, SciPy, and Matplotlib are provided by the distribution packages; plotting defaults to Qt5Agg unless MPLBACKEND is set (for example, Agg on headless hosts).',label:'DEBIAN / UBUNTU',meta:'amd64 · Debian 12 / Ubuntu 24.04+'},
    windows:{title:'Two ways into the same toolchain.',body:'The Windows installer creates separate Start Menu shortcuts for the terminal REPL and the Qt6 notebook GUI. It can add the CLI to your user PATH for use from a new PowerShell or Command Prompt.',label:'WINDOWS INSTALLER',meta:'x64 · per-user installation'},
    portable:{title:'A portable Linux bundle.',body:'The onedir distribution carries the Python runtime and numerical / graphics dependencies. It is built on a Debian baseline; compatibility still depends on the host Linux shared-library baseline.',label:'PORTABLE ARCHIVE',meta:'amd64 · PyInstaller onedir'},
  };
  const item=details[platform];
  return <section className="section install-section" id="install">
    <div className="install-glow"/>
    <div className="section-head"><p className="eyebrow">GET MALT ON YOUR MACHINE</p><h2>Choose your<br/><em>environment.</em></h2><p className="section-intro">Native packaging where it makes sense. A reproducible flake where it matters.</p></div>
    <div className="install-shell"><div className="install-tabs" role="tablist" aria-label="Choose an operating system">{tabs.map(t=><button role="tab" aria-selected={platform===t.id} className={platform===t.id?'active':''} key={t.id} onClick={()=>setPlatform(t.id)}>{t.label}</button>)}</div>
      <div className="install-content"><div className="install-copy"><span className="install-meta">{item.meta}</span><h3>{item.title}</h3><p>{item.body}</p>{downloads[platform].length > 0 ? <div className="downloads">{downloads[platform].map(d=><a key={d.file} className="button button-dark" href={`${RELEASE_DL}/${d.file}`}>{d.label} <small className="download-meta">{d.meta}</small></a>)}</div> : <a className="button button-dark" href={RELEASES} target="_blank" rel="noreferrer">View latest downloads <Icon name="external" size={15}/></a>}<a className="install-doc-link" href={`${RAW_DOC}docs/installation.md`} target="_blank" rel="noreferrer">Full installation guide ↗</a></div><div className="install-terminal"><div className="terminal-head"><span><i/><i/><i/></span><b>{item.label}</b><CopyButton value={commands[platform]} label="Copy"/></div><pre>{commands[platform]}</pre><div className="terminal-foot"><span>VERSION {VERSION}</span><span>DOCUMENTED COMMANDS</span></div></div></div>
    </div>
    <p className="install-caveat">Downloads and platform support are described in the installation guide. Architecture and package availability can change between releases; check the latest release assets before installing.</p>
  </section>;
}

function Features() {
  return <section className="section capabilities-section" id="capabilities">
    <div className="section-head split-head"><div><p className="eyebrow">ONE LANGUAGE, A COMPLETE TOOLCHAIN</p><h2>From matrix<br/><em>to breakpoint.</em></h2></div><p className="section-intro">The language is only one part of the experience. MALT brings numerical work, plotting, inspection, and editor tooling into one coherent environment.</p></div>
    <div className="capability-grid">
      <article className="capability-main"><div className="cap-number">01 / LANGUAGE</div><div className="matrix-visual"><div className="matrix-grid"><span>1</span><span>2</span><span>3</span><span>4</span></div><div className="matrix-eq">A<sup>2</sup> = <b>[ 7  10<br/>15  22 ]</b></div></div><h3>Familiar syntax.<br/>Defined behavior.</h3><p>One-based indexing, matrix and element-wise operators, complex numbers, functions, cells, structs, and control flow — all described by a real language specification.</p><a href={`${RAW_DOC}docs/semantics.md`} target="_blank" rel="noreferrer">Explore semantics <Icon name="arrow" size={14}/></a></article>
      <article className="capability-card numerical"><div className="cap-number">02 / NUMERICAL</div><div className="numerical-art"><div className="math-symbol">∫</div><div className="math-lines"><span/><span/><span/><span/></div><small>NUMPY / SCIPY</small></div><h3>Numerics, not just syntax.</h3><p>Linear algebra, reductions, calculus, root finding, and ODE solving backed by NumPy and SciPy.</p><a href={`${RAW_DOC}docs/language-support.md`} target="_blank" rel="noreferrer">See supported routines <Icon name="arrow" size={14}/></a></article>
      <article className="capability-card graphics"><div className="cap-number">03 / GRAPHICS</div><div className="mini-plot"><PlotPreview/></div><h3>Make the result visible.</h3><p>2-D and 3-D plotting, surfaces, images, subplots, legends, and headless PNG export through Matplotlib.</p><a href={`${RAW_DOC}examples/graphics`} target="_blank" rel="noreferrer">Browse graphics examples <Icon name="arrow" size={14}/></a></article>
      <article className="capability-card tools"><div className="cap-number">04 / DEVELOPER TOOLS</div><div className="tools-art"><div className="tools-line"><span>malt debug model.m</span><b>↵</b></div><div className="tools-line"><span>breakpoint · line 24</span><i>READY</i></div><div className="tools-line"><span>source map resolved</span><i className="green">OK</i></div></div><h3>Built to be explored.</h3><p>Source-aware diagnostics, a debugger, persistent REPL, Qt6 notebook GUI, and an LSP server for editor integration.</p><a href={`${RAW_DOC}docs/editor-integration.md`} target="_blank" rel="noreferrer">Explore developer tools <Icon name="arrow" size={14}/></a></article>
    </div>
  </section>;
}

function Contact() {
  return <section className="contact-section" id="contact"><div className="contact-inner"><div className="contact-mark"><img src="/assets/apple-touch-icon.png" alt="MALT gradient mark"/></div><p className="eyebrow">AN OPEN PROJECT, BUILT WITH CURIOSITY</p><h2>Make the machinery<br/><em>visible.</em></h2><p className="contact-copy">MALT is an exploration of language design, numerical computing, and the tools that make complex systems easier to understand. Read the code, try the language, or get in touch.</p><div className="contact-actions"><a className="button button-light" href={REPO} target="_blank" rel="noreferrer"><Icon name="github" size={16}/> Explore on GitHub <Icon name="external" size={14}/></a><a className="button button-outline" href="mailto:kamal@aferiad.xyz"><Icon name="mail" size={16}/> kamal@aferiad.xyz</a></div><div className="contact-rule"><span>INDEPENDENT OPEN-SOURCE PROJECT</span><span>BUILT TO BE READ</span></div></div></section>;
}

function App() {
  const [menuOpen,setMenuOpen]=useState(false);
  useEffect(()=>{
    document.body.classList.toggle('menu-open',menuOpen);
    function onKeyDown(event: KeyboardEvent) { if (event.key === 'Escape') setMenuOpen(false); }
    window.addEventListener('keydown', onKeyDown);
    return()=>{ document.body.classList.remove('menu-open'); window.removeEventListener('keydown', onKeyDown); };
  },[menuOpen]);
  const nav=[['Overview','#overview'],['Capabilities','#capabilities'],['Architecture','#architecture'],['Docs','#documentation'],['Install','#install']];
  return <>
    <header className="site-header"><div className="nav-wrap"><a className="brand" href="#overview" aria-label="MALT home"><img src="/assets/apple-touch-icon.png" alt=""/><span>MALT</span></a><nav id="primary-navigation" className={menuOpen?'nav-links open':'nav-links'} aria-label="Main navigation">{nav.map(([label,href])=><a key={href} href={href} onClick={()=>setMenuOpen(false)}>{label}</a>)}<a className="nav-github" href={REPO} target="_blank" rel="noreferrer"><Icon name="github" size={15}/> GitHub</a></nav><a className="nav-cta" href={RELEASES} target="_blank" rel="noreferrer">Get MALT <Icon name="arrow" size={14}/></a><button className="mobile-toggle" onClick={()=>setMenuOpen(!menuOpen)} aria-label={menuOpen?'Close menu':'Open menu'} aria-expanded={menuOpen} aria-controls="primary-navigation"><Icon name={menuOpen?'close':'menu'} size={21}/></button></div></header>
    <main>
      <section className="hero section" id="overview"><div className="hero-copy"><div className="version-chip"><span className="chip-dot"/> VERSION {VERSION} <span className="chip-divider">/</span> MATLAB-LIKE LANGUAGE</div><h1>Make the<br/><em>machinery</em><br/>visible.</h1><p className="hero-lede">A MATLAB-like language with a compiler you can inspect, a numerical runtime you can use, and tools that make the whole process easier to understand.</p><div className="hero-actions"><a className="button button-primary" href="#try-it">Explore the language <Icon name="arrow" size={16}/></a><a className="button button-quiet" href={REPO} target="_blank" rel="noreferrer">View on GitHub <Icon name="external" size={14}/></a><a className="button button-quiet" href={RELEASES} target="_blank" rel="noreferrer">Download <Icon name="external" size={14}/></a></div><div className="hero-proof"><div><b>01</b><span>One-based<br/>semantics</span></div><div><b>02</b><span>Readable Python<br/>generation</span></div><div><b>03</b><span>Native numerical<br/>runtime</span></div></div></div><div className="hero-visual"><WaveArt/><div className="hero-logo-float"><img src="/assets/apple-touch-icon.png" alt="MALT mark"/></div></div><div className="hero-bottom"><span>AN OPEN-SOURCE LANGUAGE IMPLEMENTATION</span><span>SCROLL TO EXPLORE <b>↓</b></span></div></section>
      <CodeWorkbench/>
      <Features/>
      <Architecture/>
      <Compatibility/>
      <Documentation/>
      <Installation/>
      <Contact/>
    </main>
    <footer className="site-footer"><a className="footer-brand" href="#overview"><img src="/assets/apple-touch-icon.png" alt=""/> MALT</a><span>© {new Date().getFullYear()} MALT · MIT License</span><div><a href={`${RAW_DOC}README.md`} target="_blank" rel="noreferrer">Documentation</a><a href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a><a href="mailto:kamal@aferiad.xyz">Contact</a></div></footer>
  </>;
}

export default App;
