/**
 * ESLint rule — flag JSX elements that render Arabic content (marked
 * via `lang="ar"` or `dir="rtl"`) but whose className does NOT include
 * the `font-arabic` Tailwind class.
 *
 * Background: this codebase had a class of latent bug where Arabic
 * text was rendered with the browser's default serif font (via
 * Tailwind's `font-serif` utility OR no font class at all). System
 * serif fonts mis-position diacritics — most notably the kasra under
 * shadda becomes visually indistinguishable from fatha, so the verse
 * 68:2 `رَبِّكَ` (rabbi-ka) rendered as `رَبَّكَ` (rabba-ka). That
 * matters a great deal for a Quran site, where the diacritics ARE
 * the content. A repo-wide sweep fixed 18 occurrences; this rule
 * keeps the bug from re-entering the codebase via new components.
 *
 * What's flagged:
 *   <p lang="ar">…</p>                                       ✗ no className
 *   <p lang="ar" className="text-xl">…</p>                   ✗ no font-arabic
 *   <p dir="rtl" className="font-serif">…</p>                ✗ wrong font
 *   <p lang="ar" className="font-arabic text-xl">…</p>       ✓ OK
 *
 * Exemptions:
 *   - Container-only elements that hold children which set their own
 *     font (e.g. <div dir="rtl"> wrapping <p className="font-arabic">).
 *     The rule can't reliably tell from a single JSX node whether its
 *     children carry the font, so we add `data-allow-no-font-arabic`
 *     as an opt-out attribute. The repo currently has a handful of
 *     these (mostly wrapper divs); we annotate them rather than
 *     dilute the rule.
 *   - Elements where `font-arabic` appears in any utility class
 *     present in className (string literals, template literals, and
 *     conditional expressions are all walked).
 *
 * Fix hint: add `font-arabic` to className. If the element is a
 * wrapper whose children handle the font, add the
 * `data-allow-no-font-arabic` opt-out attribute instead.
 */

/** @type {import('eslint').Rule.RuleModule} */
export default {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Require font-arabic on JSX elements marked as Arabic ' +
        '(lang="ar" or dir="rtl") to ensure Uthmani diacritics ' +
        'render correctly.',
    },
    schema: [],
    messages: {
      missing:
        '{{tag}} is marked Arabic ({{marker}}) but className is ' +
        'missing the font-arabic class. System fonts mis-render ' +
        'kasra-under-shadda. Add `font-arabic` to className, or ' +
        '(for wrapper elements whose children set the font) add ' +
        'the `data-allow-no-font-arabic` opt-out attribute.',
      wrongFont:
        '{{tag}} is marked Arabic ({{marker}}) and uses ' +
        '`font-serif` in its className. System serif fonts ' +
        'mis-render Arabic diacritics. Replace with ' +
        '`font-arabic`.',
    },
  },

  create(context) {
    // ----- Helpers -------------------------------------------------------

    /**
     * Pull out the static string content of a JSX className attribute.
     * Handles plain string literals AND template literals (since the
     * codebase commonly does className={`base ${cond}`}). Conditional
     * expressions and identifier references are flattened to their
     * string parts only — anything non-static (e.g. a variable holding
     * unknown classes) is conservatively treated as "may contain
     * font-arabic" so we don't false-positive.
     */
    function classNameValue(attr) {
      if (!attr) return { text: '', mayBeDynamic: false };
      const v = attr.value;
      if (!v) return { text: '', mayBeDynamic: false };

      if (v.type === 'Literal' && typeof v.value === 'string') {
        return { text: v.value, mayBeDynamic: false };
      }
      if (v.type === 'JSXExpressionContainer') {
        return walk(v.expression);
      }
      return { text: '', mayBeDynamic: true };
    }

    function walk(node) {
      if (!node) return { text: '', mayBeDynamic: false };
      switch (node.type) {
        case 'Literal':
          return {
            text: typeof node.value === 'string' ? node.value : '',
            mayBeDynamic: false,
          };
        case 'TemplateLiteral': {
          const fixed = node.quasis.map((q) => q.value.cooked).join(' ');
          // Walk each expression inside the template — concatenation
          // of conditionals like (x ? 'font-arabic' : '').
          let dyn = false;
          let extra = '';
          for (const expr of node.expressions) {
            const r = walk(expr);
            extra += ' ' + r.text;
            dyn = dyn || r.mayBeDynamic;
          }
          return { text: fixed + ' ' + extra, mayBeDynamic: dyn };
        }
        case 'ConditionalExpression': {
          // Both branches are visible classes — concatenate strings,
          // mark dynamic only if either branch is non-string.
          const c = walk(node.consequent);
          const a = walk(node.alternate);
          return {
            text: c.text + ' ' + a.text,
            mayBeDynamic: c.mayBeDynamic || a.mayBeDynamic,
          };
        }
        case 'LogicalExpression': {
          // x && 'cls'  → 'cls' visible
          const l = walk(node.left);
          const r = walk(node.right);
          return {
            text: l.text + ' ' + r.text,
            mayBeDynamic: l.mayBeDynamic || r.mayBeDynamic,
          };
        }
        case 'BinaryExpression':
          if (node.operator === '+') {
            const l = walk(node.left);
            const r = walk(node.right);
            return {
              text: l.text + ' ' + r.text,
              mayBeDynamic: l.mayBeDynamic || r.mayBeDynamic,
            };
          }
          return { text: '', mayBeDynamic: true };
        case 'ArrayExpression': {
          // ['a', 'b', cond && 'c'].join(' ')
          let txt = '';
          let dyn = false;
          for (const el of node.elements) {
            if (!el) continue;
            const r = walk(el);
            txt += ' ' + r.text;
            dyn = dyn || r.mayBeDynamic;
          }
          return { text: txt, mayBeDynamic: dyn };
        }
        case 'CallExpression': {
          // clsx('a', cond && 'b', { 'c': cond2 })
          let txt = '';
          let dyn = false;
          for (const arg of node.arguments) {
            const r = walk(arg);
            txt += ' ' + r.text;
            dyn = dyn || r.mayBeDynamic;
          }
          return { text: txt, mayBeDynamic: dyn };
        }
        case 'ObjectExpression': {
          // { 'foo': cond, 'bar': cond2 } — keys are literal classes
          let txt = '';
          for (const prop of node.properties) {
            if (prop.type === 'Property' && prop.key) {
              if (prop.key.type === 'Literal') txt += ' ' + prop.key.value;
              else if (prop.key.type === 'Identifier') txt += ' ' + prop.key.name;
            }
          }
          return { text: txt, mayBeDynamic: true };
        }
        case 'Identifier':
          // Bare identifier — we don't know what it is. Conservatively
          // mark dynamic so the element isn't flagged as missing.
          return { text: '', mayBeDynamic: true };
        default:
          return { text: '', mayBeDynamic: true };
      }
    }

    /** Extract the literal value of a JSX attribute (lang, dir). */
    function attrLiteral(attr) {
      if (!attr || !attr.value) return null;
      if (attr.value.type === 'Literal') return String(attr.value.value || '');
      if (attr.value.type === 'JSXExpressionContainer' &&
          attr.value.expression.type === 'Literal') {
        return String(attr.value.expression.value || '');
      }
      return null;
    }

    function tagName(node) {
      const open = node.openingElement || node;
      const name = open.name;
      if (!name) return '<element>';
      if (name.type === 'JSXIdentifier') return `<${name.name}>`;
      if (name.type === 'JSXMemberExpression') {
        let cur = name; let parts = [];
        while (cur.type === 'JSXMemberExpression') {
          parts.unshift(cur.property.name);
          cur = cur.object;
        }
        parts.unshift(cur.name);
        return `<${parts.join('.')}>`;
      }
      return '<element>';
    }

    // Self-closing / metadata-style tags that don't render Arabic
    // visually — exempt by name.
    const NON_VISUAL_TAGS = new Set([
      'img', 'input', 'link', 'meta', 'br', 'hr', 'source', 'track',
    ]);

    // ----- Visitor -------------------------------------------------------

    return {
      JSXOpeningElement(node) {
        const tag = tagName(node);
        if (NON_VISUAL_TAGS.has(tag.replace(/[<>]/g, ''))) return;

        let langAr = false;
        let dirRtl = false;
        let classNameAttr = null;
        let optOut = false;

        for (const a of node.attributes) {
          if (a.type !== 'JSXAttribute') continue;          if (!a.name) continue;
          const n = a.name.name;
          if (n === 'lang') {
            if (attrLiteral(a) === 'ar') langAr = true;
          } else if (n === 'dir') {
            if (attrLiteral(a) === 'rtl') dirRtl = true;
          } else if (n === 'className') {
            classNameAttr = a;
          } else if (n === 'data-allow-no-font-arabic') {
            optOut = true;
          }
        }

        if (!(langAr || dirRtl)) return;
        if (optOut) return;

        const marker = langAr ? 'lang="ar"' : 'dir="rtl"';
        const { text, mayBeDynamic } = classNameValue(classNameAttr);

        // If className has font-arabic anywhere in it, we're good.
        if (/\bfont-arabic\b/.test(text)) return;

        // If className contains font-serif explicitly, that's the
        // specific bug — flag with a clearer message.
        if (/\bfont-serif\b/.test(text)) {
          context.report({
            node, messageId: 'wrongFont', data: { tag, marker },
          });
          return;
        }

        // Dynamic className (variable reference, unknown call). We
        // can't tell whether font-arabic is set, so don't false-
        // positive. The opt-out attribute is the escape hatch for
        // intentionally-dynamic cases.
        if (mayBeDynamic) return;

        context.report({
          node, messageId: 'missing', data: { tag, marker },
        });
      },
    };
  },
};
