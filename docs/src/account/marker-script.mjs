// The account app at app.legesher.io signs readers in. While a reader is
// signed in, their browser holds a sign-in marker cookie for legesher.io: a
// timestamp, or `0` once they sign out. It carries no name, email or account
// ID. The app writes it under a plain name and under a per-instance name (the
// plain name plus a suffix).
//
// Which marker decides: a per-instance one when the browser holds any, else
// the plain one. This site does not know which suffix is current, so one
// signed-in per-instance marker is enough. The marker can also outlive a
// session that lapsed without a sign-out; that reader is shown the account
// link and the app asks them to sign in.
//
// This function runs inline in every page's <head>, before first paint, and
// only sets `data-account="signed-in"` on <html> so CSS can swap the link
// (src/components/AccountLink.astro). It makes no request, sets no cookie and
// loads no sign-in code. Anything unexpected, a missing marker included,
// leaves the page as it was built: signed out.
//
// It is serialized with toString(), so it must stay self-contained and
// comment-free inside: every character of the body ships in every page.
function readAccountMarker() {
  try {
    var own = null;
    var plain = null;
    document.cookie.split(';').forEach(function (pair) {
      var at = pair.indexOf('=');
      if (at < 0) return;
      var name = pair.slice(0, at).trim();
      var on = /^[1-9][0-9]{0,15}$/.test(pair.slice(at + 1).trim());
      if (name === '__client_uat') plain = on;
      else if (name.indexOf('__client_uat_') === 0) own = own || on;
    });
    if (own === null ? plain : own) document.documentElement.dataset.account = 'signed-in';
  } catch (e) {}
}

export const ACCOUNT_MARKER_SCRIPT = `(${readAccountMarker.toString()})();`;
