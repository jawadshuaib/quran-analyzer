import { useEffect } from 'react';

const SITE_NAME = 'al-nuqta';
const SITE_URL = 'https://al-nuqta.com';
const DEFAULT_OG_IMAGE = `${SITE_URL}/og-image.png`;

interface SEOProps {
  title: string;
  description: string;
  path?: string;
  ogImage?: string;
  noindex?: boolean;
}

function setMetaTag(property: string, content: string, isOg = false) {
  const attr = isOg ? 'property' : 'name';
  let el = document.querySelector(`meta[${attr}="${property}"]`) as HTMLMetaElement | null;
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, property);
    document.head.appendChild(el);
  }
  el.content = content;
}

function setCanonical(url: string) {
  let el = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (!el) {
    el = document.createElement('link');
    el.rel = 'canonical';
    document.head.appendChild(el);
  }
  el.href = url;
}

/**
 * Sets document title, meta description, Open Graph tags, and canonical URL.
 * Call once per route/page component.
 */
export function useSEO({ title, description, path, ogImage, noindex }: SEOProps) {
  useEffect(() => {
    // Title
    document.title = `${title} | ${SITE_NAME}`;

    // Meta description
    setMetaTag('description', description);

    // Open Graph
    setMetaTag('og:title', title, true);
    setMetaTag('og:description', description, true);
    setMetaTag('og:site_name', SITE_NAME, true);
    setMetaTag('og:type', 'website', true);
    setMetaTag('og:image', ogImage || DEFAULT_OG_IMAGE, true);

    if (path) {
      const canonicalUrl = `${SITE_URL}${path}`;
      setMetaTag('og:url', canonicalUrl, true);
      setCanonical(canonicalUrl);
    }

    // Twitter Card
    setMetaTag('twitter:card', 'summary_large_image');
    setMetaTag('twitter:title', title);
    setMetaTag('twitter:description', description);
    setMetaTag('twitter:image', ogImage || DEFAULT_OG_IMAGE);

    // Robots
    if (noindex) {
      setMetaTag('robots', 'noindex, nofollow');
    } else {
      // Remove noindex if previously set
      const robotsMeta = document.querySelector('meta[name="robots"]');
      if (robotsMeta) robotsMeta.remove();
    }
  }, [title, description, path, ogImage, noindex]);
}
