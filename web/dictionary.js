(() => {
  const search = document.getElementById('word-search');
  const list = document.getElementById('word-list');
  const status = document.getElementById('dictionary-status');
  const retry = document.getElementById('dictionary-retry');
  const selection = document.getElementById('dictionary-selection');
  const panel = document.getElementById('dictionary-panel');
  const opener = document.getElementById('dictionary-open');
  const close = document.getElementById('dictionary-close');
  const done = document.getElementById('dictionary-done');
  let returnToText = false;
  let words = [];

  opener.addEventListener('click', () => {
    returnToText = false;
    panel.showModal(); // Native focus containment and Escape support.
    opener.setAttribute('aria-expanded', 'true');
    document.body.classList.add('dictionary-open');
    (search.disabled ? close : search).focus();
  });
  close.addEventListener('click', () => panel.close());
  panel.addEventListener('keydown', event => {
    // Search inputs can consume Escape to clear their value; always close here.
    if (event.key === 'Escape') {
      event.preventDefault();
      panel.close();
    }
    if (event.key === 'Tab') {
      const items = [...panel.querySelectorAll('button:not(:disabled), input:not(:disabled)')]
        .filter(item => !item.hidden && item.getClientRects().length);
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  done.addEventListener('click', () => {
    returnToText = true;
    panel.close();
  });
  panel.addEventListener('close', () => {
    document.body.classList.remove('dictionary-open');
    opener.setAttribute('aria-expanded', 'false');
    (returnToText ? document.getElementById('text') : opener).focus();
  });
  panel.addEventListener('click', event => {
    const rect = panel.getBoundingClientRect();
    if (event.target === panel && (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom)) panel.close();
  });

  function render() {
    const query = search.value.trim().toLowerCase();
    const matches = words.filter(word => word.toLowerCase().includes(query));
    list.replaceChildren();
    status.textContent = matches.length
      ? `${matches.length} of ${words.length} words and phrases`
      : 'No matching words. Try another search; unsupported words cannot generate a sign.';
    const fragment = document.createDocumentFragment();
    for (const word of matches) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn';
      button.textContent = word;
      button.setAttribute('aria-label', `Add ${word} to text`);
      button.addEventListener('click', () => {
        const input = document.getElementById('text');
        input.value = [input.value.trim(), word].filter(Boolean).join(' ');
        input.dispatchEvent(new Event('input', {bubbles: true}));
        selection.textContent = `Added "${word}". Select Generate motion when ready.`;
      });
      fragment.appendChild(button);
    }
    list.appendChild(fragment);
  }

  async function load() {
    retry.hidden = true;
    search.disabled = true;
    status.textContent = 'Loading dictionary...';
    try {
      const response = await fetch('/api/dictionary');
      if (!response.ok) throw new Error('Dictionary unavailable');
      const data = await response.json();
      if (!Array.isArray(data.words) || !data.words.every(word => typeof word === 'string')) {
        throw new Error('Invalid dictionary');
      }
      words = [...new Set(data.words)].sort();
      search.disabled = false;
      render();
      if (!words.length) status.textContent = 'No signs are available yet.';
    } catch {
      status.textContent = 'Could not load the dictionary. Please retry.';
      retry.hidden = false;
    }
  }
  search.addEventListener('input', render);
  retry.addEventListener('click', load);
  load();
})();
