import asyncio
import re
from playwright.async_api import async_playwright


async def main():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto('https://www.taptap.cn/app/230531/review?sort=new', wait_until='domcontentloaded', timeout=60000)
    await page.wait_for_timeout(8000)
    html = await page.content()
    classes = sorted(set(re.findall(r'class="([^"]+)"', html)))
    hits = [c for c in classes if ('review' in c.lower() or 'comment' in c.lower())]
    print('html_len=', len(html))
    print('review_like_classes=', hits[:200])
    print('contains_review_item=', '.review-item' in html)
    print('contains_data_id=', 'data-id=' in html)
    print(html[:2000])
    await browser.close()
    await p.stop()


if __name__ == '__main__':
    asyncio.run(main())
