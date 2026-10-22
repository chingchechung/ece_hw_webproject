// UI capabilities only. Educational rules always take precedence over URL flags.
export function toolFlags(url) {
  const query = new URL(url).searchParams;
  return { presenter: query.get('presenter') === '1', debug: query.get('debug') === '1' };
}
export function toolPolicy(flags, educational) {
  return { presenter: Boolean(flags.presenter && !educational), debug: Boolean(flags.debug && !educational) };
}
export function playerUrl(url) {
  const result = new URL(url);
  result.searchParams.delete('presenter'); result.searchParams.delete('debug');
  return result;
}
