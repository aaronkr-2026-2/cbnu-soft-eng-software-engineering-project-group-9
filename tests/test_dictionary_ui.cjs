// Lightweight DOM regression checks: node --test tests/test_dictionary_ui.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/dictionary.js', 'utf8');

class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  replaceChildren() { this.children = []; }
  appendChild(child) {
    if (child.fragment) this.children.push(...child.children);
    else this.children.push(child);
  }
  setAttribute(name, value) { this[name] = value; }
  focus() { this.focused = true; }
  showModal() { this.open = true; }
  close() { this.open = false; this.listeners.close(); }
  dispatchEvent() {}
}

async function setup(fetch) {
  const elements = {};
  const document = {
    body: {classList: {add() {}, remove() {}}},
    getElementById: id => elements[id] ||= new Element(),
    createElement: () => new Element(),
    createDocumentFragment: () => Object.assign(new Element(), {fragment: true}),
  };
  vm.runInNewContext(source, {document, fetch, Event: class {}});
  await new Promise(resolve => setImmediate(resolve));
  return elements;
}

test('search is case-insensitive, phrases append intact, empty results explain why', async () => {
  const e = await setup(async () => ({ok: true, json: async () => ({words: ['coffee', 'thank you', 'hello']})}));
  assert.equal(e['word-list'].children.length, 3);
  e['word-search'].value = ' THANK ';
  e['word-search'].listeners.input();
  assert.equal(e['word-list'].children[0].textContent, 'thank you');
  // The text field is looked up only on selection.
  e['word-list'].children[0].listeners.click();
  assert.equal(e.text.value, 'thank you');
  e['word-list'].children[0].listeners.click();
  assert.equal(e.text.value, 'thank you thank you');
  e['word-search'].value = 'unknownword';
  e['word-search'].listeners.input();
  assert.equal(e['word-list'].children.length, 0);
  assert.match(e['dictionary-status'].textContent, /No matching/);
});

test('network failure offers retry and recovers', async () => {
  let fail = true;
  const e = await setup(async () => {
    if (fail) throw new Error('offline');
    return {ok: true, json: async () => ({words: ['hello']})};
  });
  assert.equal(e['dictionary-retry'].hidden, false);
  assert.equal(e['word-search'].disabled, true);
  fail = false;
  await e['dictionary-retry'].listeners.click();
  assert.equal(e['word-search'].disabled, false);
  assert.equal(e['word-list'].children.length, 1);
});

test('sidebar opens, closes and returns to the text input on Done', async () => {
  const e = await setup(async () => ({ok: true, json: async () => ({words: ['coffee']})}));
  e['dictionary-open'].listeners.click();
  assert.equal(e['dictionary-panel'].open, true);
  assert.equal(e['dictionary-open']['aria-expanded'], 'true');
  assert.equal(e['word-search'].focused, true);
  e['dictionary-close'].listeners.click();
  assert.equal(e['dictionary-panel'].open, false);
  assert.equal(e['dictionary-open']['aria-expanded'], 'false');
  e['dictionary-open'].listeners.click();
  e['dictionary-done'].listeners.click();
  assert.equal(e.text.focused, true);
});
