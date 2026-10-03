(() => {
  const form = document.querySelector('[data-search-geography]');
  if (!form) return;
  const fields = ['region', 'province', 'city', 'zone', 'postal_code'];
  const selects = Object.fromEntries(fields.map(name => [name, form.elements[name]]));
  const original = Object.fromEntries(fields.map(name => [name, Array.from(selects[name].options).map(option => option.cloneNode(true))]));
  const selected = name => Array.from(selects[name].selectedOptions).map(option => option.value);
  function restrict(name, parents) {
    const values = selected(name);
    const options = original[name].filter(option => (option.dataset.parents || '').split(',').some(parent => parents.includes(parent)));
    selects[name].replaceChildren(...options.map(option => {
      const copy = option.cloneNode(true);
      copy.selected = values.includes(copy.value);
      return copy;
    }));
  }
  function refresh() {
    const regions = selected('region');
    restrict('province', regions.length ? regions : original.region.map(option => option.value));
    const provinces = selected('province');
    restrict('city', provinces.length ? provinces : Array.from(selects.province.options).map(option => option.value));
    const cities = selected('city');
    const allowed = cities.length ? cities : Array.from(selects.city.options).map(option => option.value);
    restrict('zone', allowed);
    restrict('postal_code', allowed);
  }
  for (const name of ['region', 'province', 'city']) selects[name].addEventListener('change', refresh);
  refresh();
})();
