# What may transfer, and what may not

Confidence key: 🟢 published primary source · 🟡 secondary, jurisdiction-dependent, confirm locally · 🔴 folklore.
Not legal advice. Confirm with a trademark attorney in the market where the brand will trade.

## Method transfers. Marks do not.

| Transfers (value-free) | Does not transfer |
|---|---|
| Stage order and gate questions | The name, or anything close to it |
| "One warm hue over half the surface, one cool hue for proof" | The hex values |
| "Fuse an origin cue into a letter counter" | The glyph, its shape or its phrase |
| Serif/sans contrast pairing by role | The same licensed typeface as a signature |
| Photography rules (no faces, brand ground colour) | The photographs |

`method_transfer_guard.py` enforces the left column by blocking value leaks in patterns and
near-clones in the new brief.

## Why distinctiveness is the thing to protect

1. 🟢 Byron Sharp, *How Brands Grow*, Oxford University Press, 2010. Brands grow through
   mental and physical availability; distinctive assets (colour, shape, line, character) are
   how a buyer recognises a brand without reading its name.
2. 🟢 Jenni Romaniuk, *Building Distinctive Brand Assets*, Oxford University Press, 2018.
   Assets are judged on fame and uniqueness. A copied asset is famous but not unique to you,
   so it builds the reference brand's memory, not yours.

## Law the guard approximates (not a substitute for a search)

3. 🟡 Brazil, Lei 9.279/1996 (Lei da Propriedade Industrial), art. 124, item XIX: reproduction
   or imitation, in whole or in part, of another's registered mark for identical, similar or
   related goods or services, liable to cause confusion or association, cannot be registered.
   Check the current text and INPI practice. Also Lei 9.610/1998 for copyright in artwork.
4. 🟢 United States, Lanham Act, 15 U.S.C. section 1114 and section 1125(a): likelihood of
   confusion. Courts weigh several factors; the classic list is
   *Polaroid Corp. v. Polarad Electronics Corp.*, 287 F.2d 492 (2d Cir. 1961).
5. 🟢 European Union, Regulation (EU) 2017/1001, art. 8(1)(b): refusal where identity or
   similarity of marks and goods creates a likelihood of confusion.
6. 🟢 WIPO, Nice Classification: goods and services are grouped in classes. Same sector
   usually means same or related class, which is why SAME_SECTOR raises every warning.

## Guard thresholds are tool heuristics

🟡 The numbers (name similarity 0.80, delta-E 10, word overlap 50%) are conservative working
limits chosen to catch obvious copies. No court applies them. A DISTANT verdict means "no
obvious overlap found", never "cleared".

## Folklore to refuse

- 🔴 "Change three things and it is legal." There is no such rule. Confusion is judged on the
  overall impression.
- 🔴 "A bought font is free to use in a logo." Licences differ for desktop, web, app and
  logo use. Read the end-user licence.
- 🔴 "It is only inspiration if I do not trace it." Close adaptation of a distinctive asset
  can still confuse buyers and still infringe.
