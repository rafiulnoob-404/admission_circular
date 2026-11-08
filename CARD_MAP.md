# CARD MAP — কোনটা কোথায় বসে + GPA ↔ eligibility ফ্লো

> শুধু পয়েন্ট। কোথায় কী বসবে, কোন অর্ডারে, আর Elig//যোগ্যতা কীভাবে GPA থেকে আসে।
> আপডেট: ৭ নভেম্বর ২০২৬

> **এই রিপোতে:** আলাদা `build_cards.py` / `build_eligibility.py` / `unis.json` নেই — `index.html`-এর
> ভেতরে `card-data` JSON মিরর + রেডি মার্কআপ, আর `eligibility.html`-এ `UNIS` অবজেক্ট আছে।
> নিচের নিয়মগুলো ওই দুই ফাইলের কাঠামো ও ফ্লো বোঝাতে ব্যবহার হবে।

---

## ১. কার্ডের ভেতরের অর্ডার

1. `article.card.p-<palette>` — সব কিছুর খোলস · `data-file` = শর্ট নাম
2. `.top` → `.names` (`.bnname` + `.enname`) + `.sealwrap` (`.refpill`? + `.seal`)
3. `.chips` — প্রোগ্রাম · ধরন · সময়
4. `.hero-date` — **শুধু** সোর্স নেই এমন কার্ডে
5. `.dstrip` — আবেদন · সময়কাল · যোগ্য তালিকা · ক্লাস · ফলাফল (+ রেফ-কার্ডে প্রথমে ভর্তি পরীক্ষা)
6. `.unit-table` — `unit_list` থাকলে
7. `.sub-table` — `subjects` থাকলে
8. `.lb-items` — `list_blocks` (নির্বাচন প্রক্রিয়া, নোট)
9. `.grid` → Elig//যোগ্যতা ব্লক → ফিল্ড (আসন · কেন্দ্র · ফি · মোট নম্বর · নেগেটিভ)
10. `.srcbox` — `source_url` থাকলে (ব্যাজ + উদ্ধৃতি + লিংক)
11. `.foot` — সাইট লিংক + `.dlbtn`

---

## ২. কোন ডেটা কোথায় যায়

| ফিল্ড | বসে | দেখাবে না যখন |
|---|---|---|
| `exam_date` | `.hero-date` **বা** `.dstrip` প্রথম সারি | ফাঁকা হলে ঘর বাদ |
| `apply_start` / `apply_end` | `.dstrip` → আবেদন | দুটোই ফাঁকা |
| `apply_window` | `.dstrip` → আবেদনের সময়কাল | ফাঁকা |
| `shortlist_date` | `.dstrip` → যোগ্য তালিকা | ফাঁকা |
| `class_start` / `result_date` | `.dstrip` শেষ সারি | ফাঁকা |
| `unit_list[]` | `.unit-table` | লিস্ট নেই |
| `subjects[]` + `total` | `.sub-table` | লিস্ট নেই |
| `marks` | গ্রিড → মোট নম্বর | `subjects.total` থাকলে বাদ |
| `negative` · `seats` · `centers` · `fee` | গ্রিডের ফিল্ড | ফাঁকা হলে ওই ঘর বাদ |
| `elig_rules[]` / `elig_items[]` / `elig_label` | Elig//যোগ্যতা ব্লক | তিনটাই ফাঁকা |
| `switch_note` | Elig ব্লকের শেষ লাইন | ফাঁকা |
| `source_url{}` | `.srcbox` + `.refpill` + ফুটার লিংক | `url` নেই |
| `palette` | `p-*` ক্লাস | না দিলে ক্রম অনুযায়ী |
| `year_label` | ফুটার সেশন | ডিফল্ট ২০২৬ |

---

## ৩. Elig//যোগ্যতা কোথায় বসে (কার্ডে)

- জায়গা: `.grid`-এর **প্রথম ঘর**, `wide` — বাকি ফিল্ড দুই কলামে
- শিরোনাম সবসময় `.lbl` = `Elig//যোগ্যতা`, আইকন সহ — আলাদা "এলিজিবিলিটি" শিরোনাম নেই
- বডি: `.lb-items.elist` → প্রতিটা নিয়ম ১ বুলেট
- `elig_rules` > `elig_items` > `elig_label` (এই ক্রমে যেটা আগে পাওয়া যায়)
- `switch_note` সবসময় শেষে: `বিভাগ পরিবর্তন: …`

---

## ৪. GPA ↔ Elig রিলেশন (গণিত)

`eligibility.html` → `check(rule, data)` · ইনপুট **৫টা**: SSC GPA · HSC GPA · গণিত · পদার্থ · রসায়ন · ইংরেজি

| নিয়ম (JSON) | তুলনা | ইনপুট উৎস |
|---|---|---|
| `ssc_gpa_min` | SSC GPA ≥ X | SSC GPA |
| `hsc_min` + `ssc_min` | HSC ≥ X · SSC ≥ Y | HSC/SSC GPA |
| `each_min` | দুটোই আলাদাভাবে ≥ X | SSC + HSC GPA |
| `combined_min` | SSC + HSC ≥ X (৪র্থ বিষয়সহ) | SSC + HSC GPA |
| `subject_sum{subjects,min}` | ওই বিষয়গুলোর GPA যোগফল ≥ X | বিষয় GPA (গণিত/পদার্থ/রসায়ন/ইংরেজি) |
| `groups[]` | HSC বিভাগ লিস্টে আছে কি না | বিভাগ সিলেক্ট |
| `ssc_years` / `hsc_year` | পাসের বছর অনুমোদিত কি না | বছর |
| `extra` | যাচাই হয় না — নোট হিসেবে দেখায় | — |

- প্রতিটা নিয়ম এক লাইন: `লেবেল` · `পাওয়া` · ✔/✘
- ৩টার বেশি চেক হলে `openAll` — একসাথে দেখায়
- কোনো নিয়ম মেলেনি → `unknown` (উত্তর নেই)
- সব মিললে `pass` ✔যোগ্য · একটাও না মিললে `fail` ✘অযোগ্য

---

## ৫. eligibility.html ওয়াক-ফ্লো

1. `index.html` → হেডারে Elig//যোগ্যতা বাটন → `eligibility.html`
2. ইনপুট: SSC GPA · HSC GPA · বিভাগ · বিষয় GPA (গণিত/পদার্থ/রসায়ন/ইংরেজি)
3. ইনপুট বদলালেই **লাইভ** হিসাব (কোনো সাবমিট নেই, কোনো গার্ড নেই)
4. ফলাফল: প্রতি ভার্সিটি ১ `.item` → `✔যোগ্য` / `✘অযোগ্য` / `unknown`
5. KPI কাউন্টার: মোট ভার্সিটি · যোগ্য · যোগ্য নয় (countUp ১১০০ms, ডিলে ৩০০/৫৫০/৮০০)
6. Elig চাপার পর **২১০০ms** পরে অটো-স্ক্রল → KPI → ফলাফল শুরু
7. `.item` স্ট্যাগার্ড ৭০ms · `.chk-line` +১২০ms · আইকন +১৬০ms
8. "← সব কার্ড দেখুন" → সরাসরি `index.html`
9. `prefers-reduced-motion` → অ্যানিমেশন বন্ধ, KPI তাৎক্ষণিক

---

## ৬. নতুন কার্ড যোগ করার ক্রম

1. ডেটা: `index.html`-এর `card-data` JSON (+ রেডি মার্কআপ) · `eligibility.html`-এর `UNIS`
2. দরকার হলে নতুন `.p-*` প্যালেট (STYLE_GUIDE §১)
3. `eligibility.html` → `SWITCH["শর্ট"]` (বিভাগ পরিবর্তন নোট) থাকলে
4. দুই ফাইলের ডেটা একসাথে আপডেট — কার্ড, Elig রুল, ক্যালেন্ডারে তারিখ (থাকলে)
5. অডিট: কার্ড সংখ্যা · Elig লাইন · `font < 8.5 → ০` · HTML ট্যাগ ব্যালেন্স · `node --check` (ইনলাইন JS)
6. PDF রি-এক্সপোর্ট → প্রতিটা পেজে টেক্সট আছে কি না
7. `README.md`-এ লগ · নিয়ম বদলালে `STYLE_GUIDE.md` / `CARD_MAP.md` আপডেট
