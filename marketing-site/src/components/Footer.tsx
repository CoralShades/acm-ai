import Link from "next/link";
import Image from "next/image";
import { APP_URL } from "@/lib/site-urls";

const footerLinks: Record<string, Array<{ label: string; href: string; external?: boolean }>> = {
  Product: [
    { label: "Open App", href: APP_URL, external: true },
    { label: "Demo", href: "/demo" },
    { label: "Documentation", href: "/docs" },
    { label: "Status", href: "/status" },
    { label: "Roadmap", href: "/roadmap" },
  ],
  Technology: [
    { label: "Next.js 15", href: "https://nextjs.org" },
    { label: "FastAPI", href: "https://fastapi.tiangolo.com" },
    { label: "SurrealDB", href: "https://surrealdb.com" },
    { label: "LangGraph", href: "https://langchain-ai.github.io/langgraph" },
  ],
  Compliance: [
    { label: "Victorian BAR Format", href: "/docs/guides/bar-compliance" },
    { label: "47-Column Schema", href: "/docs/prd/data-model" },
    { label: "WCAG 2.1 AA", href: "/docs/architecture" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-border bg-vaea-navy text-white/70">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <Image
                src="/acm-logo-bg.svg"
                alt="ACM-AI logo"
                width={32}
                height={32}
                className="h-8 w-8 rounded-lg"
              />
              <span className="font-[family-name:var(--font-dm-serif)] text-lg text-white">
                ACM-AI
              </span>
            </div>
            <p className="text-sm leading-relaxed">
              Asbestos Compliance Intelligence for the Victorian Government.
              Transforming PDF registers into BAR-compliant data with AI.
            </p>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-vaea-teal-500/15 px-3 py-1 text-xs font-semibold text-vaea-teal-100">
              <span className="h-1.5 w-1.5 rounded-full bg-vaea-teal-300" />
              Feature Complete
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/40">
                {category}
              </h3>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      target={link.external ? "_blank" : undefined}
                      rel={link.external ? "noopener noreferrer" : undefined}
                      className="text-sm transition-colors hover:text-vaea-teal-100"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 border-t border-white/10 pt-8 text-center text-xs text-white/30">
          <p>Built with Next.js, FastAPI, SurrealDB, and LangGraph. Powered by VAEA.</p>
        </div>
      </div>
    </footer>
  );
}
