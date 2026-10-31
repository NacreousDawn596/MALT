import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

/** Resolve a relative link against a base doc path (repo-root relative). */
export function resolveDocPath(basePath: string, href: string): string {
  const clean = href.split(/[?#]/)[0];
  const baseDir = basePath.split('/').slice(0, -1).join('/');
  const joined = baseDir ? `${baseDir}/${clean}` : clean;
  const stack: string[] = [];
  for (const part of joined.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') stack.pop();
    else stack.push(part);
  }
  return stack.join('/');
}

/** True when a markdown link href should open inside the reader. */
export function isDocLink(href: string): boolean {
  if (!href) return false;
  return !/^(https?:|mailto:|tel:|#|\/\/)/i.test(href);
}

export function Markdown({
  source,
  basePath,
  onNavigate,
}: {
  source: string;
  basePath: string;
  onNavigate?: (path: string) => void;
}) {
  const components: Components = {
    a({ href, children, ...props }) {
      if (href && isDocLink(href)) {
        const target = resolveDocPath(basePath, href);
        return (
          <a
            href={`#${target}`}
            onClick={(e) => {
              e.preventDefault();
              onNavigate?.(target);
            }}
            {...props}
          >
            {children}
          </a>
        );
      }
      const external = /^https?:/i.test(href || '');
      return (
        <a
          href={href}
          target={external ? '_blank' : undefined}
          rel={external ? 'noreferrer' : undefined}
          {...props}
        >
          {children}
        </a>
      );
    },
    img({ src, alt }) {
      return <img src={src} alt={alt ?? ''} loading="lazy" />;
    },
  };

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
