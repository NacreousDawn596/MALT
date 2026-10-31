import { useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { docs, RAW_DOC } from './data';
import { Icon } from './Icon';
import { Markdown } from './Markdown';

type OpenDoc = { path: string };

export function Documentation() {
  const [query, setQuery] = useState('');
  const [active, setActive] = useState<OpenDoc | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        document.getElementById('documentation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        searchRef.current?.focus();
      }
    }
    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);

  const filtered = useMemo(
    () => docs.filter((d) => `${d.title} ${d.group} ${d.description} ${d.tags}`.toLowerCase().includes(query.toLowerCase().trim())),
    [query],
  );
  const groups = Array.from(new Set(filtered.map((d) => d.group)));

  return (
    <section className="section documentation-section" id="documentation">
      <div className="section-head split-head">
        <div>
          <p className="eyebrow">THE REFERENCE SHELF</p>
          <h2>Made to be<br /><em>understood.</em></h2>
        </div>
        <p className="section-intro">The implementation is documented from the language rules down to the runtime API. Pick a document to read it right here — no tab-hopping to GitHub.</p>
      </div>
      <div className="docs-search">
        <Icon name="search" size={18} />
        <input
          ref={searchRef}
          value={query}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
          placeholder="Search the documentation…"
          aria-label="Search documentation"
        />
        <kbd>⌘ K&nbsp; · &nbsp;Ctrl K</kbd>
        {query && <button onClick={() => setQuery('')} aria-label="Clear search">×</button>}
      </div>
      <div className="docs-groups">
        {groups.length
          ? groups.map((group) => (
              <div className="docs-group" key={group}>
                <h3>{group}</h3>
                <div className="docs-items">
                  {filtered.filter((d) => d.group === group).map((d) => (
                    <button
                      className="doc-item"
                      key={d.path}
                      onClick={() => setActive({ path: d.path })}
                      aria-label={`Read ${d.title}`}
                    >
                      <div><strong>{d.title}</strong><p>{d.description}</p></div>
                      <span className="doc-path">{d.path}</span>
                      <span className="doc-arrow"><Icon name="external" size={15} /></span>
                    </button>
                  ))}
                </div>
              </div>
            ))
          : <p className="empty-state">No documents match “{query}”. Try a different term.</p>}
      </div>
      <a className="text-link" href={`${RAW_DOC}docs`} target="_blank" rel="noreferrer">Explore all documentation <Icon name="arrow" size={15} /></a>

      {active && <DocReader path={active.path} onClose={() => setActive(null)} />}
    </section>
  );
}

function DocReader({ path, onClose }: { path: string; onClose: () => void }) {
  const [activePath, setActivePath] = useState(path);
  const [source, setSource] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setSource(null);
    setError(null);
    fetch(`/${activePath}`)
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.text();
      })
      .then((text) => { if (!cancelled) setSource(text); })
      .catch(() => { if (!cancelled) setError(`Could not load “${activePath}”.`); });
    return () => { cancelled = true; };
  }, [activePath]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) { if (event.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    document.body.classList.add('reader-open');
    return () => document.body.classList.remove('reader-open');
  }, []);

  useEffect(() => { scrollRef.current?.scrollTo({ top: 0 }); }, [activePath]);

  const displayTitle = useMemo(() => {
    const match = docs.find((d) => d.path === activePath);
    if (match) return match.title;
    const base = activePath.split('/').pop()?.replace(/\.md$/i, '').replace(/[-_]/g, ' ') ?? activePath;
    return base.charAt(0).toUpperCase() + base.slice(1);
  }, [activePath]);

  return (
    <div className="doc-reader" role="dialog" aria-modal="true" aria-label={displayTitle}>
      <div className="doc-reader-bar">
        <div className="doc-reader-bar-inner">
          <button className="doc-reader-close" onClick={onClose} aria-label="Close document">
            <Icon name="back" size={19} />
            <span>All docs</span>
          </button>
          <span className="doc-reader-path">{activePath}</span>
          <a className="doc-reader-github" href={`${RAW_DOC}${activePath}`} target="_blank" rel="noreferrer">
            View on GitHub <Icon name="external" size={13} />
          </a>
        </div>
      </div>
      <div className="doc-reader-scroll" ref={scrollRef}>
        <article className="doc-reader-article">
          {error && <p className="doc-reader-status">{error}</p>}
          {!error && source === null && <p className="doc-reader-status">Loading…</p>}
          {!error && source !== null && <Markdown source={source} basePath={activePath} onNavigate={setActivePath} />}
        </article>
      </div>
    </div>
  );
}
