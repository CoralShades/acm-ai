"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/cn";
import { APP_URL } from "@/lib/site-urls";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/demo", label: "Demo" },
  { href: "/docs", label: "Docs" },
  { href: "/status", label: "Status" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/architecture", label: "Architecture", isNew: true },
];

export function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <Image
            src="/acm-logo-bg.svg"
            alt="ACM-AI logo"
            width={32}
            height={32}
            className="h-8 w-8 rounded-lg"
            priority
          />
          <span className="font-[family-name:var(--font-dm-serif)] text-lg font-normal tracking-tight text-foreground">
            ACM-AI
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-vaea-teal-500/10 text-vaea-teal-700"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {link.label}
                {link.isNew && (
                  <span className="inline-flex items-center rounded-full bg-vaea-coral px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">
                    New
                  </span>
                )}
              </Link>
            );
          })}
          <Link
            href={APP_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 rounded-lg bg-vaea-coral px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:brightness-110"
          >
            Open App
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-border bg-background px-6 py-4 md:hidden">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-vaea-teal-500/10 text-vaea-teal-700"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {link.label}
                {link.isNew && (
                  <span className="inline-flex items-center rounded-full bg-vaea-coral px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">
                    New
                  </span>
                )}
              </Link>
            );
          })}
          <Link
            href={APP_URL}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setMobileOpen(false)}
            className="mt-2 block rounded-lg bg-vaea-coral px-3 py-2.5 text-sm font-semibold text-white transition-colors hover:brightness-110"
          >
            Open App
          </Link>
        </div>
      )}
    </header>
  );
}
