(() => {
  const ids = ['region', 'province', 'municipality', 'postal_code', 'zone'];
  const selects = Object.fromEntries(ids.map(name => [name, document.querySelector(`[name="${name}"]`)]));
  if (!selects.region || !selects.municipality) return;
  const originals = Object.fromEntries(ids.slice(1).map(name => [name, Array.from(selects[name].options).map(option => option.cloneNode(true))]));
  function restrict(name, parent) {
    const select = selects[name];
    const oldValue = select.value;
    const allowed = originals[name].filter(option => !option.value || (parent && (option.dataset.parents || '').split(',').includes(parent)));
    select.replaceChildren(...allowed.map(option => option.cloneNode(true)));
    select.value = allowed.some(option => option.value === oldValue) ? oldValue : '';
  }
  function refresh() {
    restrict('province', selects.region.value);
    restrict('municipality', selects.province.value);
    restrict('postal_code', selects.municipality.value);
    restrict('zone', selects.municipality.value);
  }
  for (const name of ['region', 'province', 'municipality']) selects[name].addEventListener('change', refresh);
  refresh();
})();
