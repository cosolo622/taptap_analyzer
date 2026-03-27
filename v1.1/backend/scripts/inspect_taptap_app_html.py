import re
import requests


def main():
    html = requests.get('https://www.taptap.cn/app/230531', headers={'User-Agent': 'Mozilla/5.0'}, timeout=30).text
    print('len=', len(html))
    print('has_webapiv2=', 'webapiv2' in html)
    print('review_count=', len(re.findall('review', html.lower())))
    urls = set(re.findall(r'https?://[^"\'\s]+', html))
    web_urls = [u for u in urls if 'tap' in u.lower() or 'webapi' in u.lower()]
    print('urls_sample=', web_urls[:50])
    for key in ['webapiv2', 'review', 'comment', 'X-UA', 'api']:
        if key in html:
            print('contains', key)


if __name__ == '__main__':
    main()
