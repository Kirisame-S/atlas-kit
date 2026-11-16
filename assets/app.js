'use strict';

document.querySelectorAll('[data-enhanced]').forEach(element => { element.hidden = false; });

const cards = Array.from(document.querySelectorAll('[data-entry]'));
const search = document.querySelector('#search');
let selectedCategory = 'all';

function filterEntries() {
  const term = search.value.trim().toLocaleLowerCase();
  let count = 0;
  cards.forEach(card => {
    const matches = (selectedCategory === 'all' || card.dataset.category === selectedCategory)
      && card.dataset.search.toLocaleLowerCase().includes(term);
    card.hidden = !matches;
    if (matches) count += 1;
  });
  document.querySelector('#result-count').textContent = `${count} / ${cards.length} 個觀念`;
  document.querySelector('#empty').hidden = count !== 0;
}

if (search) {
  search.addEventListener('input', filterEntries);
  const filters = document.querySelectorAll('.filter');
  filters.forEach(button => button.addEventListener('click', () => {
    selectedCategory = button.dataset.category;
    filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    filterEntries();
  }));
  document.querySelector('#reset-search').addEventListener('click', () => {
    search.value = '';
    selectedCategory = 'all';
    filters.forEach(item => item.setAttribute('aria-pressed', String(item.dataset.category === 'all')));
    filterEntries();
    search.focus();
  });
}

document.querySelectorAll('[data-comparison]').forEach(comparison => {
  const panels = comparison.querySelectorAll('[data-panel]');
  const buttons = comparison.querySelectorAll('[data-view]');
  // Without JavaScript both examples remain visible in the generated HTML.
  function select(view) {
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
    panels.forEach(panel => { panel.hidden = panel.dataset.panel !== view; });
  }
  buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.view)));
  select('before');
});

const copyButton = document.querySelector('#copy-prompt');
if (copyButton) {
  copyButton.addEventListener('click', async () => {
    const prompt = document.querySelector('#prompt-text');
    const status = document.querySelector('#copy-status');
    try {
      await navigator.clipboard.writeText(prompt.textContent);
      status.textContent = '已複製。';
    } catch {
      const range = document.createRange();
      range.selectNodeContents(prompt);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = '已選取文字，請使用複製快捷鍵。';
    }
  });
}
