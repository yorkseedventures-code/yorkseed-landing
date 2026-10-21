// Scraper shield for yorkseed.co and list.yorkseed.co.
// 1. Search engines, AI search crawlers and link previews always get through (we want to rank there).
// 2. Known scraping tools and SEO-copy bots get a 403.
// 3. The raw event data files only load inside our own pages, not when fetched directly by a script.
const GOOD = /(googlebot|google-inspectiontool|googleother|storebot-google|adsbot-google|mediapartners-google|bingbot|bingpreview|msnbot|duckduckbot|duckassistbot|yandex|baiduspider|applebot|slurp|gptbot|oai-searchbot|chatgpt-user|claudebot|claude-user|claude-searchbot|claude-web|anthropic-ai|perplexitybot|perplexity-user|youbot|amazonbot|meta-externalagent|meta-externalfetcher|facebookexternalhit|facebookcatalog|linkedinbot|twitterbot|slackbot|discordbot|telegrambot|whatsapp|skypeuripreview|pinterestbot|redditbot|embedly|iframely|mistralai-user|cohere-ai|google-extended|applebot-extended|ccbot|diffbot)/i;
const BAD = /(python-requests|python-urllib|python\/|aiohttp|httpx|scrapy|curl\/|wget|go-http-client|node-fetch|axios|undici|okhttp|java\/|libwww|lwp::|httpclient|http_request|guzzle|headlesschrome|phantomjs|puppeteer|playwright|selenium|colly|crawler4j|nutch|heritrix|ahrefsbot|semrushbot|mj12bot|dotbot|petalbot|dataforseobot|serpstatbot|blexbot|zoominfobot|barkrowler|seekportbot|megaindex|screaming frog|sitebulb|bytespider|imagesiftbot|scrapingbee|scraperapi|zenrows|apify|brightdata|octoparse|parsehub|webcopier|httrack|offline explorer|teleport)/i;
const DATA = /^\/(?:list\/)?(?:data\/|events\.json|feed\.json|banners\.json)/;
const OURS = /^https:\/\/((www\.|list\.)?yorkseed\.co|[a-z0-9-]+\.netlify\.app|([a-z0-9-]+\.)*claudeusercontent\.com|claude\.ai)(\/|$)/i;

export default async (request, context) => {
  const ua = request.headers.get("user-agent") || "";
  const path = new URL(request.url).pathname;
  const good = GOOD.test(ua);
  const deny = (msg) => new Response(msg, { status: 403, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });

  if (!good && (!ua.trim() || BAD.test(ua))) return deny("Automated access to Yorkseed is not permitted. Contact info@yorkseed.co for partnerships.");

  if (DATA.test(path) && !good) {
    const site = request.headers.get("sec-fetch-site") || "";
    const from = request.headers.get("origin") || request.headers.get("referer") || "";
    if (!(site === "same-origin" || site === "same-site" || OURS.test(from))) return deny("This data is only available on The Yorkseed List: https://list.yorkseed.co/");
  }
  return context.next();
};

export const config = {
  path: "/*",
  excludedPath: ["/.netlify/*", "/assets/*", "/*.css", "/*.js", "/*.png", "/*.jpg", "/*.jpeg", "/*.webp", "/*.svg", "/*.ico", "/*.woff2", "/*.woff"],
};
