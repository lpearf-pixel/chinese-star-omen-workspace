# B10 C24 source comparison

## Scope and current disposition

Case `C24` is anchored at `卷38 / KR3g0018_WYG_038-13b`. It remains a
research candidate with `ambiguous`, `not_computable` and high evidence risk.
This note does not replace either human reviewer and does not approve a citable
rule.

## Direct observations

1. `038-13b` begins inside **填星流動與列星鬭八**. The complete carrier
   text is:

   > 郗萌曰填星變色逆行相凌而鬬㑹客環守其國無道

2. The next heading is explicit: **填星穰氣暈彗九**. The fish-shaped qi and
   dog-shaped cloud belong to this new section, not to the preceding
   `客環守` clause.
3. The Wikisource revision and the pinned Kanripo WYG transcription preserve
   the same unpunctuated character string at this point. CText adds punctuation,
   but it is an editorial presentation of the same text, not an independent
   textual witness.
4. The two labels `雒書` and `洛書` both occur within this short context.
   They are recorded as witness-level variants and must not be silently merged
   in the source layer.

## Parallel formula inside the same work

| Planet | Locator | Exact middle formula |
|---|---|---|
| 歲星 | `KR3g0018_WYG_023-21a` | `嵗星變色逆行相凌而鬬舍合留舍環守其國無道` |
| 熒惑 | `KR3g0018_WYG_030-21b` | `熒惑變色逆行相凌而鬬㑹舍還其國無道` |
| 填星 | `KR3g0018_WYG_038-13b` | `填星變色逆行相凌而鬬㑹客環守其國無道` |

The stable frame is `planet + 變色 + 逆行 + 相凌而鬭 + disputed middle +
其國無道`. The middle segment differs across the three planetary chapters.

## Competing segmentation hypotheses

| ID | Segmentation | Supporting evidence | Contrary evidence | Confidence |
|---|---|---|---|---|
| H1 | `會客／環守` | `客` can denote a guest body and `守` is an established stationary relation | no operative distance or duration; no identical parallel formula found | low |
| H2 | corrupted member of the repeated `舍合留／舍環守` formula | the 歲星 chapter supplies a structurally complete parallel | the character sequence does not yield a secure one-step emendation | medium-low |
| H3 | `會客環守` as one compound relation | matches later editorial punctuation | no independent lexical definition or threshold found | low |

No hypothesis is approved. A scan-level or independent-edition witness is
required before choosing a reading.

## Atomic passage split proposed for review

| Candidate | Carrier source | Observation | Omen/result | Present status |
|---|---|---|---|---|
| C24-A | 郗萌 | 填星變色、逆行、相凌而鬭、 disputed middle | 其國無道 | keep ambiguous; not citable |
| C24-B | 洛書 | 填星珥魚; note says qi like a fish beside Saturn | 黃帝起 (historical association) | descriptive threshold absent |
| C24-C | 黃帝占 | cloud beside Saturn, shaped like a dog | 土功; one-month term | shape threshold absent |
| C24-D | 孝經內記 | Saturn produces yellow `穰` qi | weather, grain price and illness sequence | compound; split further |
| C24-E | 荊州占 | Saturn emits `穰氣`, length four 丈 | one reading says raining earth | length present; geometry/unit unresolved |
| C24-F | 巫咸 | Saturn self-haloes | earthworks and mourning | halo threshold absent |
| C24-G | 郗萌 | Saturn emits a broom/comet-like ray | country below receives war and loses land within one year | relation to true comet unresolved |

## Citation decision

- `Formal candidate`: **YES**, after splitting into C24-A through C24-G.
- `Citation eligible`: **NO** for the current combined passage.
- `Eligibility`: **needs_review / ambiguous**, not `eligible`.
- 《黃帝占》 and 《洛書》 are not treated as independently downloaded complete
  books. In this research pass, their recoverable evidence is the quotation
  carried by 《唐開元占經》; no complete standalone witness was located.

## Sources

- Wikisource, revision 655950:
  https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷038&oldid=655950
- Kanripo WYG transcription, pinned commit:
  https://github.com/kanripo/KR3g0018/commit/eb17a11a6a8a40922ccff01f727e2b5df7f3e734
- CText editorial comparison:
  https://ctext.org/wiki.pl?chapter=955155&if=gb
