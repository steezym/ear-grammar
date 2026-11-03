"""Generate the 🔊 audio for a week page with one neural voice (no API key needed).

Usage:  python tools/make_audio.py speaking/week-01
Needs:  pip install edge-tts   (only on the computer that makes the audio)

Collects every text the page can read aloud (data-say="..." attributes, and the
q / model of "speak" exercises), saves one MP3 per text in <week>/audio/, and
writes <week>/audio/manifest.json mapping text -> file. Re-run after editing texts;
unchanged texts are not generated again.
"""
import asyncio
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "-5%"


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def texts_in(page):
    source = page.read_text(encoding="utf-8")
    found = [html.unescape(t) for t in re.findall(r'data-say="([^"]+)"', source)]
    for block in re.findall(r'\{\s*type:\s*"speak".*?checks:', source, flags=re.S):
        for field in ("q", "model"):
            m = re.search(field + r':\s*"((?:[^"\\]|\\.)*)"', block)
            if m:
                found.append(html.unescape(re.sub(r"<[^>]+>", "", m.group(1).replace('\\"', '"'))))
    return list(dict.fromkeys(norm(t) for t in found))


async def main(week):
    week = Path(week)
    out = week / "audio"
    out.mkdir(exist_ok=True)
    manifest = {}
    for text in texts_in(week / "index.html"):
        name = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + ".mp3"
        target = out / name
        if not target.exists() or target.stat().st_size == 0:
            tmp = target.with_suffix(".part")  # a failed download never leaves a broken .mp3 behind
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(tmp))
            if tmp.stat().st_size == 0:
                tmp.unlink()
                sys.exit("No audio received for: " + text)
            tmp.replace(target)
            print("made", name, "<-", text[:60])
        manifest[text] = name
    for old in out.glob("*.mp3"):  # drop audio for texts that no longer exist
        if old.name not in manifest.values():
            old.unlink()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(manifest), "audio files in", out)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
