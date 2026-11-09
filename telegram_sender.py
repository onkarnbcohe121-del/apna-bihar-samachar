#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram edition post — Bot API se (Web login ki zarurat nahi).
telegram_edition/ folder me: card.png, edition.txt, proof_*.png (optional).
Kram: (A) card photo + caption, (B) text edition, (C) har proof photo.
Safalta par telegram_edition/POSTED_<stamp>.txt receipt likhta hai."""
import glob, os, sys, time
import urllib.request, urllib.parse, urllib.error
import json, uuid, mimetypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.environ.get("TELEGRAM_CHAT_ID", "@ApnaBiharSamachar").strip()
BASE = f"https://api.telegram.org/bot{TOKEN}"
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_edition')


def post_form(method, fields, file_field=None, file_path=None):
    boundary = '----juno' + uuid.uuid4().hex
    body = b''
    for k, v in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode('utf-8')
    if file_field and file_path:
        mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        with open(file_path, 'rb') as f:
            data = f.read()
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
                 f'filename="{os.path.basename(file_path)}"\r\nContent-Type: {mime}\r\n\r\n').encode('utf-8')
        body += data + b'\r\n'
    body += f'--{boundary}--\r\n'.encode('utf-8')
    req = urllib.request.Request(f'{BASE}/{method}', data=body, method='POST',
                                 headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    if not out.get('ok'):
        raise SystemExit(f'{method} failed: {out}')
    return out['result']


def post_json(method, payload):
    req = urllib.request.Request(f'{BASE}/{method}',
                                 data=json.dumps(payload).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    if not out.get('ok'):
        raise SystemExit(f'{method} failed: {out}')
    return out['result']


def main():
    if not TOKEN:
        raise SystemExit('TELEGRAM_BOT_TOKEN missing')
    card = os.path.join(DIR, 'card.png')
    text_file = os.path.join(DIR, 'edition.txt')
    if not os.path.exists(text_file):
        raise SystemExit('edition.txt nahi mili — post skip')
    text = open(text_file, encoding='utf-8').read().strip()
    caption = ''
    for line in text.splitlines():
        if line.strip():
            caption = line.strip()
            break
    sent = []
    if os.path.exists(card):
        r = post_form('sendPhoto', {'chat_id': CHAT, 'caption': caption + '\nपूरी खबरें नीचे 👇'},
                      'photo', card)
        sent.append(('card', r['message_id']))
        time.sleep(2)
    # text edition — 4096 seema, hisso me
    chunks, cur = [], ''
    for line in text.splitlines(keepends=True):
        if len(cur) + len(line) > 3800 and cur:
            chunks.append(cur)
            cur = ''
        cur += line
    if cur:
        chunks.append(cur)
    for c in chunks:
        r = post_json('sendMessage', {'chat_id': CHAT, 'text': c,
                                      'disable_web_page_preview': False})
        sent.append(('text', r['message_id']))
        time.sleep(2)
    for proof in sorted(glob.glob(os.path.join(DIR, 'proof_*.png'))):
        cap_file = proof + '.caption.txt'
        cap = open(cap_file, encoding='utf-8').read().strip() if os.path.exists(cap_file) else ''
        r = post_form('sendPhoto', {'chat_id': CHAT, 'caption': cap}, 'photo', proof)
        sent.append(('proof', r['message_id']))
        time.sleep(2)
    stamp = time.strftime('%Y%m%d_%H%M')
    with open(os.path.join(DIR, f'POSTED_{stamp}.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(f'{k}: {v}' for k, v in sent))
    print('POSTED OK:', sent)


if __name__ == '__main__':
    main()
