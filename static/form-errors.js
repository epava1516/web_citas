/* Recover error context after a server-rendered form rejection. No data is sent. */
(() => {
  // Respect native autofocus or focus deliberately set by another component.
  if (document.activeElement !== document.body) return;
  const error = Array.from(document.querySelectorAll('#main form .errorlist')).find(
    element => element.textContent.trim() && element.getClientRects().length &&
      getComputedStyle(element).visibility !== 'hidden'
  );
  if (!error) return;
  error.setAttribute('tabindex', '-1');
  error.focus();
})();
