# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Generate the mechanical volume family for wave 8 (length/bullet/word
counts over realistic base passages) and merge with probes3.json.

Usage: python gen_probes3.py  -> writes probes3_full.json
"""

import json
import os

BASE = os.path.dirname(__file__)

PASSAGES = [
    "The meeting was moved to Thursday afternoon because the main speaker "
    "has a prior commitment, and the new time suits most of the team.",
    "Your refund has been processed and should appear in your account within "
    "five working days, depending on your bank.",
    "The new release fixes the login issue, improves page load times by "
    "twenty percent, and adds dark mode support across the whole app.",
    "The package was delivered to the front desk this morning and is ready "
    "for collection using the reference number you received by email.",
    "The workshop starts at nine sharp in the main hall, and light refreshments "
    "will be served in the foyer before the first session begins.",
    "The contractor has confirmed that the roof repairs will be completed by "
    "the end of next week, weather permitting, at the quoted price.",
    "The survey results show that most customers are happy with the service, "
    "with the main area for improvement being response times on weekends.",
    "The training module takes about forty minutes to complete, and a short "
    "quiz at the end confirms that the key points have been understood.",
]


def bullets(text: str, n: int) -> str:
    # split into n pseudo-bullets by sentences/clauses
    words = text.split()
    per = max(1, len(words) // n)
    parts = []
    for i in range(n):
        chunk = words[i * per : (i + 1) * per if i < n - 1 else len(words)]
        parts.append("- " + " ".join(chunk))
    return "\n".join(parts)


def numbered(text: str, n: int) -> str:
    words = text.split()
    per = max(1, len(words) // n)
    parts = []
    for i in range(n):
        chunk = words[i * per : (i + 1) * per if i < n - 1 else len(words)]
        parts.append(f"{i + 1}. " + " ".join(chunk))
    return "\n".join(parts)


def sentences(text: str, n: int) -> str:
    words = text.split()
    per = max(1, len(words) // n)
    parts = []
    for i in range(n):
        chunk = words[i * per : (i + 1) * per if i < n - 1 else len(words)]
        s = " ".join(chunk)
        parts.append(s[0].upper() + s[1:] + ".")
    return " ".join(parts)


probes = []
for pi, passage in enumerate(PASSAGES):
    nwords = len(passage.split())
    nb = bullets(passage, 3)
    nn = numbered(passage, 3)
    ns = sentences(passage, 2)
    # word-count family (boundary-aware)
    probes += [
        {"id": f"gen_w_{pi}_maxmet", "response": sentences(passage, 1)[:180],
         "requirement": f"The response uses at most {nwords + 4} words.", "met": True},
        {"id": f"gen_w_{pi}_maxnot", "response": passage + " " + passage[:60],
         "requirement": f"The response uses at most {nwords + 2} words.", "met": False},
        # bullet-count family
        {"id": f"gen_b_{pi}_3met", "response": nb,
         "requirement": "The response uses exactly 3 bullet points.", "met": True},
        {"id": f"gen_b_{pi}_3not2", "response": bullets(passage, 2),
         "requirement": "The response uses exactly 3 bullet points.", "met": False},
        {"id": f"gen_b_{pi}_3not4", "response": bullets(passage, 4),
         "requirement": "The response uses exactly 3 bullet points.", "met": False},
        # numbered-vs-bullet family
        {"id": f"gen_n_{pi}_not", "response": nn,
         "requirement": "The response uses bullet points, not numbered items.", "met": False},
        {"id": f"gen_n_{pi}_nummet", "response": nn,
         "requirement": "The response uses exactly 3 numbered items.", "met": True},
        # sentence-count family
        {"id": f"gen_s_{pi}_2met", "response": ns,
         "requirement": "The response is exactly two sentences.", "met": True},
        {"id": f"gen_s_{pi}_1not", "response": sentences(passage, 1),
         "requirement": "The response is exactly two sentences.", "met": False},
    ]

# merge
hand = json.load(open(os.path.join(BASE, "probes3.json")))
out = {"note": hand["note"] + " Generated families: word-count, bullet-count, numbered, sentence-count.",
       "probes": hand["probes"] + probes}
json.dump(out, open(os.path.join(BASE, "probes3_full.json"), "w"), indent=2)
print(f"total probes: {len(out['probes'])} ({len(hand['probes'])} hand + {len(probes)} generated)")
