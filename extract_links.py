#!/usr/bin/env python3
"""
FuckingFast Direct Link Extractor v9.0 (Final)
===============================================
Extracts direct download links from fuckingfast.co landing pages.

How it works:
1. GET the landing page with curl_cffi (bypasses Cloudflare)
2. Parse the HTMX button to find the POST endpoint (/f/{id}/go)
3. POST to that endpoint with HX-Request header
4. Extract the direct /dl/ link from the HX-Redirect response header

Usage:
    python extract_links.py -i links.txt -o direct.txt
    python extract_links.py -u "https://fuckingfast.co/xxxxx#file.rar"

Requirements:
    pip install curl_cffi beautifulsoup4
"""

import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    from curl_cffi import requests
except ImportError:
    print("[ERROR] curl_cffi not installed. Run: pip install curl_cffi")
    sys.exit(1)

from bs4 import BeautifulSoup


def get_direct_link(url: str) -> str | None:
    """Extract direct download link from a single fuckingfast.co URL."""
    file_id = urlparse(url).path.strip('/')
    if not file_id:
        return None

    try:
        # Step 1: GET landing page (curl_cffi bypasses Cloudflare)
        resp = requests.get(url, impersonate="chrome", timeout=30)
        if resp.status_code != 200:
            return None

        # Step 2: Parse HTMX endpoint from download button
        soup = BeautifulSoup(resp.text, 'html.parser')
        btn = soup.find('a', attrs={'hx-post': True})
        hx_post = btn.get('hx-post') if btn else f"/f/{file_id}/go"

        # Step 3: POST to HTMX endpoint
        post_url = f"https://fuckingfast.co{hx_post}" if hx_post.startswith(
            '/') else f"https://fuckingfast.co/{hx_post}"
        post_headers = {
            'HX-Request': 'true',
            'HX-Current-URL': url,
            'Referer': url,
            'Origin': 'https://fuckingfast.co',
        }

        post_resp = requests.post(
            post_url,
            headers=post_headers,
            data='',
            impersonate="chrome",
            timeout=30,
            allow_redirects=False
        )

        # Step 4: Extract direct link from HX-Redirect header
        hx_redirect = post_resp.headers.get('HX-Redirect', '')
        if hx_redirect and '/dl/' in hx_redirect:
            return hx_redirect

        # Fallback: check Location header
        location = post_resp.headers.get('Location', '')
        if location and '/dl/' in location:
            return location

        return None

    except Exception as e:
        print(f"  [ERR] {type(e).__name__}: {e}")
        return None


def process_file(input_file: str, output_file: str, delay: int = 2):
    """Batch process a file of fuckingfast.co URLs."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_file}")
        sys.exit(1)

    urls = [l.strip() for l in input_path.read_text().splitlines()
            if l.strip() and 'fuckingfast.co' in l]

    if not urls:
        print("[ERROR] No valid fuckingfast.co URLs found.")
        sys.exit(1)

    print(f"[*] Processing {len(urls)} links...\n")

    direct_links = []
    failed = []

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url.split('#')[0][-50:]}")
        link = get_direct_link(url)
        if link:
            direct_links.append(link)
            print(f"  [✓] {link[:80]}...")
        else:
            failed.append(url)
            print(f"  [✗] Failed")

        # Rate limiting between requests
        if i < len(urls):
            time.sleep(delay)

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(direct_links))

    print(f"\n{'='*60}")
    print(f"[✓] Success: {len(direct_links)}/{len(urls)} links extracted")
    print(f"[✓] Saved to: {output_path.absolute()}")

    if failed:
        fail_file = output_path.with_suffix('.failed.txt')
        fail_file.write_text("\n".join(failed))
        print(f"[!] Failed ({len(failed)}): {fail_file.absolute()}")

    print(f"\n[>] Use with download managers:")
    print(f"    aria2c -i {output_path.name} -d /path/to/download -j 5 -x 5")
    print(f"    wget -i {output_path.name}")
    print(f"    IDM: File > Import > From text file")


def main():
    parser = argparse.ArgumentParser(
        description="Extract direct /dl/ links from fuckingfast.co (v9.0 Final)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_links.py -i links.txt -o direct.txt
  python extract_links.py -u "https://fuckingfast.co/xxxxx#file.rar"
        """
    )
    parser.add_argument(
        '-i', '--input', help='File with fuckingfast.co URLs (one per line)')
    parser.add_argument(
        '-o', '--output', default='direct_links.txt', help='Output file')
    parser.add_argument('-u', '--url', help='Process a single URL')
    parser.add_argument('--delay', type=int, default=2,
                        help='Seconds between requests (default: 2)')

    args = parser.parse_args()

    if args.url:
        print(f"[*] Processing single URL...\n")
        link = get_direct_link(args.url)
        print(f"\n{'='*60}")
        if link:
            print(f"[✓] DIRECT LINK:\n{link}")
        else:
            print("[✗] Failed.")
            sys.exit(1)
    elif args.input:
        process_file(args.input, args.output, args.delay)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
