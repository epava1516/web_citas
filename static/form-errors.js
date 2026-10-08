/* Recover error context after a server-rendered form rejection. No data is sent. */
(() => {
  const recover = () => {
    const main = document.getElementById('main');
    // A retained skip-link fragment can take focus after deferred scripts run.
    // Preserve native autofocus and explicit focus in other controls.
    if (document.activeElement !== document.body &&
        !(location.hash === '#main' && document.activeElement === main)) return;
    const error = Array.from(document.querySelectorAll('#main form .errorlist')).find(
      element => element.textContent.trim() && element.getClientRects().length &&
        getComputedStyle(element).visibility !== 'hidden'
    );
    if (!error) return;
    error.setAttribute('tabindex', '-1');
    error.focus();
  };
  const afterLoad = () => requestAnimationFrame(recover);
  if (document.readyState === 'complete') afterLoad();
  else window.addEventListener('load', afterLoad, {once: true});
})();
