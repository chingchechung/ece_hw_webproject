/* v1 URL patterns from schemas/assignment-v1.schema.json; parity checked in tests. */
(function (root) {
  "use strict";
  const rules = Object.freeze({
  "youtubeUrl": "^https://(?:(?:www\\.)?youtube\\.com/watch\\?(?:(?!v=)[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*&)*v=(?!(?:[xX]{11}|[yY]{11}|[zZ]{11}|0{11}|_{11}|-{11})(?:[?&#/]|$))[A-Za-z0-9_-]{11}(?:&(?!v=)[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*)*|youtu\\.be/(?!(?:[xX]{11}|[yY]{11}|[zZ]{11}|0{11}|_{11}|-{11})(?:[?&#/]|$))[A-Za-z0-9_-]{11}(?:\\?(?!v=)[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*(?:&(?!v=)[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*)*)?)(?:#[A-Za-z0-9_=.-]+)?(?![\\s\\S])",
  "googleFormUrl": "^https://(?:forms\\.gle/(?!(?:[xX]+|[yY]+|[zZ]+|0+|_+|-+|[Pp][Ll][Aa][Cc][Ee][Hh][Oo][Ll][Dd][Ee][Rr]|[Ee][Xx][Aa][Mm][Pp][Ll][Ee]|YOUR_FORM_ID|FORM_ID)(?:[/?#]|$))[A-Za-z0-9_-]+|docs\\.google\\.com/forms/(?:u/[0-9]+/)?d/(?:e/)?(?!(?:[xX]+|[yY]+|[zZ]+|0+|_+|-+|[Pp][Ll][Aa][Cc][Ee][Hh][Oo][Ll][Dd][Ee][Rr]|[Ee][Xx][Aa][Mm][Pp][Ll][Ee]|YOUR_FORM_ID|FORM_ID)(?:[/?#]|$))[A-Za-z0-9_-]+/(?:viewform|edit))(?:\\?[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*(?:&[A-Za-z0-9_.~-]+=(?:[A-Za-z0-9_.~+/-]|%[0-9A-Fa-f]{2})*)*)?(?:#[A-Za-z0-9_=.-]+)?(?![\\s\\S])"
});
  if (typeof module === "object" && module.exports) module.exports = rules;
  else root.AssignmentRules = rules;
}(typeof globalThis !== "undefined" ? globalThis : this));
