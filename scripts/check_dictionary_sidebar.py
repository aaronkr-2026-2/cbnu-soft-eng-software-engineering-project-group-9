"""Optional browser smoke test: python scripts/check_dictionary_sidebar.py.

Requires Playwright and Microsoft Edge. Uses local files and fixture responses;
does not generate poses or depend on a running server.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    for width, height in ((1280, 900), (390, 844)):
        page = browser.new_page(viewport={'width': width, 'height': height})
        def serve(route):
            path = route.request.url.split('http://sidebar.test')[-1]
            if path == '/api/dictionary':
                route.fulfill(json={'words': ['coffee', 'hello', 'thank you']})
            elif path == '/api/health':
                route.fulfill(json={'signs': 3})
            elif path == '/api/text-to-pose':
                route.fulfill(json={'frames': [], 'matches': []})
            elif path == '/dictionary.js':
                route.fulfill(path=str(root / 'web/dictionary.js'), content_type='text/javascript')
            else:
                route.fulfill(path=str(root / 'web/index.html'), content_type='text/html')
        page.route('http://sidebar.test/**', serve)
        page.goto('http://sidebar.test/')
        assert not page.locator('#dictionary-panel').is_visible()
        page.locator('#text').fill('hello')
        page.get_by_role('button', name='Browse dictionary').click()
        page.locator('#word-search').fill('COFF')
        page.get_by_role('button', name='Add coffee to text', exact=True).click()
        assert page.locator('#text').input_value() == 'hello coffee'
        box = page.locator('#dictionary-panel').bounding_box()
        assert box['x'] >= 0 and box['x'] + box['width'] <= width + 1
        page.locator('#dictionary-done').click()
        assert page.locator('#text').evaluate('(el) => el === document.activeElement')
        page.locator('#dictionary-open').click()
        page.keyboard.press('Escape')
        page.locator('#dictionary-panel').wait_for(state='hidden')
        assert not page.locator('#dictionary-panel').is_visible()
        assert page.locator('#dictionary-open').get_attribute('aria-expanded') == 'false'
        page.locator('#dictionary-open').click()
        page.locator('#dictionary-close').focus()
        page.keyboard.press('Shift+Tab')
        assert page.locator('#dictionary-panel').evaluate('(el) => el.contains(document.activeElement)')
        if width > 440:
            page.mouse.click(10, 100)
            page.locator('#dictionary-panel').wait_for(state='hidden')
            assert not page.locator('#dictionary-panel').is_visible()
        page.close()
        print(f'Sidebar passed at {width}x{height}')
    browser.close()
