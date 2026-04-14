interface Props {
  currentPath: string;
}

const NAV_LINKS = [
  { label: 'Learn', href: '/learning' },
  { label: 'Methodology', href: '/methodology' },
  { label: 'API', href: '/developers' },
  { label: 'Settings', href: '/settings' },
];

export default function NavBar({ currentPath }: Props) {
  return (
    <nav className="w-full bg-cream/90 backdrop-blur-sm border-b border-card-border sticky top-0 z-30">
      <div className="max-w-3xl mx-auto px-4 flex items-center justify-between py-3 sm:py-4">
        <a
          href="/"
          className="font-serif text-lg sm:text-xl font-medium tracking-tight text-ink hover:opacity-80 transition-opacity"
        >
          al-nuqta
        </a>

        <div className="flex items-center gap-3 sm:gap-5 text-[12px] sm:text-[13px] text-ink-secondary">
          {NAV_LINKS.map((link) => {
            const isActive =
              link.href === '/'
                ? currentPath === '/'
                : currentPath.startsWith(link.href);

            return (
              <a
                key={link.label}
                href={link.href}
                className={`hover:text-ink transition-colors ${
                  isActive ? 'text-ink font-medium' : ''
                }`}
              >
                {link.label}
              </a>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
