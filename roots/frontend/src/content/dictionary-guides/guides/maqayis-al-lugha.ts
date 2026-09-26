import type { DictionaryGuide } from '../types';

const guide: DictionaryGuide = {
  slug: 'maqayis-al-lugha',
  dictionarySlugs: ['ibn-faris-maqayis-al-lugha'],
  title: 'Maqāyīs al-Lugha',
  titleAr: 'مقاييس اللغة',
  titleGloss: 'The Measures of Language',
  author: 'Ibn Fāris',
  authorFull: 'Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ',
  authorAr: 'ابن فارس',
  period: 'd. 395 AH / 1004–5 CE (other dates reported)',
  sortYear: 1004,
  kind: 'Root-meaning dictionary',
  summary: `Where he can, Ibn Fāris names the core sense or senses (*uṣūl*) he believed a root's words share, supports them with poetry, the Qur'an and earlier lexicons, and sets aside words that do not fit. The unifying senses are his proposals.`,
  lede: `Many dictionaries record what words mean. Ibn Fāris set out to show what holds a root's words together. A typical entry of the *Maqāyīs al-Lugha* opens with a verdict, that these letters form one *aṣl* (a root sense), or two, or three, and then brings the words, verses and older authorities that support it. Read it as it was written: as an argument by a tenth-century philologist, persuasive in places, strained in others, and frank about the words that refuse to fit.`,
  body: `## A thesis in the preface

Ibn Fāris worked mostly in Hamadhān and later at the Buyid court in Rayy, where he died. The year is variously reported: his modern editor, ʿAbd al-Salām Hārūn, lists five dates before settling on 395 AH (1004–5 CE).[^harun-ed|editor's introduction, pp. 5–10] His preface states the programme:

> إنّ للغة العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع.
> "The language of the Arabs has sound measures, and roots from which branches grow."
> — Ibn Fāris, preface (translation for this guide)[^harun-ed|vol. 1, p. 3]

Earlier compilers, he complains, never set out a single one of these measures. He has headed each section, he says, with the *aṣl* from which its details branch, so that a short statement covers the whole family.[^harun-ed|vol. 1, p. 3] His material comes from five books: al-Khalīl's [[guide:kitab-al-ayn|Kitāb al-ʿAyn]], which he ranks highest and noblest, two by Abū ʿUbayd, one by Ibn al-Sikkīt, and Ibn Durayd's *Jamhara*. Everything else, he says, rests on these.[^harun-ed|vol. 1, pp. 3–5] The words are inherited; the analysis is his.

## How an entry works

A common verdict is *aṣl ṣaḥīḥ yadullu ʿalā…*, "a sound root pointing to…", but not every root gets a sense. Of [[root:mjs|ibn-faris-maqayis-al-lugha|م ج س]], the root of *al-majūs* (Q 22:17), he writes: "a word for which we know no measure; I think it is Persian" (our translation). Here is one he does unify:

:::excerpt kfr|ibn-faris-maqayis-al-lugha
الْكَافُ وَالْفَاءُ وَالرَّاءُ أَصْلٌ صَحِيحٌ يَدُلُّ عَلَى مَعْنًى وَاحِدٍ، وَهُوَ السَّتْرُ وَالتَّغْطِيَةُ… وَيُقَالُ لِلزَّارِعِ كَافِرٌ، لِأَنَّهُ يُغَطِّي الْحَبَّ بِتُرَابِ الْأَرْضِ. قَالَ اللَّهُ تَعَالَى: {أَعْجَبَ الْكُفَّارَ نَبَاتُهُ}… وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ.
---
"Kāf, fāʾ and rāʾ are a sound root pointing to a single meaning: concealing and covering… The sower is called *kāfir* because he covers the seed with the soil of the earth. God, exalted, said: 'its growth delights the *kuffār*' [Q 57:20]… *Kufr*, the opposite of *īmān*, is so called because it is a covering of the truth."
:::

In [[root:kfr|ibn-faris-maqayis-al-lugha|ك ف ر]] the concrete uses come first: covering one's armour with a garment, ashes buried by windblown dust, verses in which the sun "casts its hand into *kāfir*", for which he reports two glosses, sunset or the sea, without choosing. The Qur'an is cited for farmers, not for belief. Only then does *kufr* appear, its link to covering stated in his own voice ("so called because"). His hedges show: low mountain passes are called *kafirāt* "perhaps" (*laʿalla*) because the high peaks seem to hide them. In his *al-Ṣāḥibī* he argues that with Islam some words moved "from their places to other places": the Arabs, he says, knew of *kufr* only covering and concealment (our translation).[^sahibi|pp. 44–45] The entry shows the word's concrete range; that "unbelief" grew out of "covering" is Ibn Fāris's reconstruction.

Misfits are set apart with a recurring formula, *wa-mimmā shadhdha ʿan hādhā l-bāb*: "among what departs from this chapter", the chapter being the root's family. Sometimes he argues the case in the open:

:::excerpt qbl|ibn-faris-maqayis-al-lugha
الْقَافُ وَالْبَاءُ وَاللَّامُ أَصْلٌ وَاحِدٌ صَحِيحٌ تَدُلُّ كَلِمُهُ كُلُّهَا عَلَى مُوَاجَهَةِ الشَّيْءِ لِلشَّيْءِ… فَأَمَّا قَبْلُ الَّذِي هُوَ خِلَافُ بَعْدَ، فَيُمْكِنُ أَنْ يَكُونَ شَاذًّا عَنِ الْأَصْلِ الَّذِي ذَكَرْنَاهُ، وَقَدْ يُتَمَحَّلُ لَهُ بِأَنْ يُقَالَ هُوَ مُقْبِلٌ عَلَى الزَّمَانِ. وَهُوَ عِنْدَنَا إِلَى الشُّذُوذِ أَقْرَبُ.
---
"Qāf, bāʾ and lām are a single sound root; all its words point to one thing facing another… As for *qabl*, the opposite of *baʿd* ['before' as against 'after'], it may be an outlier from the root sense we gave. A strained case can be made by saying that it faces toward time, but in our view it is nearer to being an outlier."
:::

So in [[root:qbl|ibn-faris-maqayis-al-lugha|ق ب ل]] the form the Qur'an uses most is placed, tentatively, outside the family. Hārūn thought Ibn Fāris hardly ever failed to find the shared sense;[^harun-ed|editor's introduction, p. 23] entries like this one let a reader test that judgment.

Under each first letter come doubled roots such as [[root:rdd|none|ر د د]] (a section missing from our copy), then three-letter roots, in an order of Ibn Fāris's own; most letters end with a chapter on longer words.[^harun-ed|editor's introduction, pp. 42–44] Of these, "most of what you see," he says, is carved (*manḥūt*): two words are taken and a new one is carved from them, keeping a share of each. The rest were "set down" with no room for measure (our translation).[^harun-ed|vol. 1, pp. 328–29] So *karbala*, a slack-footed gait, is carved from *rabl* (flabby flesh) and *kabl* (a fetter). Elsewhere he names a third kind, three-letter words with letters added.[^harun-ed|vol. 2, p. 509] *Kanfalīla*, a bushy beard, is one: *kafl* (gathering), enlarged. He also marks words as foreign or doubtful: sulphur (*kibrīt*) "is not Arabic"; of another, "I do not know how the scholars accept this and its like" (our translation).

## Two senses that pull apart

Some roots get two *uṣūl*, even when they seem to clash:

:::excerpt Ebd|ibn-faris-maqayis-al-lugha
الْعَيْنُ وَالْبَاءُ وَالدَّالُ أَصْلَانِ صَحِيحَانِ، كَأَنَّهُمَا مُتَضَادَّانِ، وَ [الْأَوَّلُ] مِنْ ذَيْنِكَ الْأَصْلَيْنِ يَدُلُّ عَلَى لِينٍ وَذُلٍّ، وَالْآخَرُ عَلَى شِدَّةٍ وَغِلَظٍ… وَمِنَ الْبَابِ الْبَعِيرُ الْمُعَبَّدُ، أَيِ الْمَهْنُوءُ بِالْقَطْرَانِ. وَهَذَا أَيْضًا يَدُلُّ عَلَى مَا قُلْنَاهُ لِأَنَّ ذَلِكَ يُذِلُّهُ وَيَخْفِضُ مِنْهُ.
---
"ʿAyn, bāʾ and dāl are two sound roots that seem to be opposites. The [first] of the two points to softness and lowliness, the other to hardness and toughness… To this family belongs *al-baʿīr al-muʿabbad*, the camel smeared with tar. This too points to what we said, because that humbles it and lowers it."
:::

(The bracketed word is the editor's.) Under the first *aṣl* of [[root:Ebd|ibn-faris-maqayis-al-lugha|ع ب د]] stand *ʿabd*, the owned servant, and the well-trodden road; under the second, cloth that is thick and strong, and *ʿabad*, indignant disdain. Some quoted voices are marked: "al-Khalīl said" introduces the distinction between God's servants (*ʿibād*) and owned slaves (*ʿabīd*). Where a quotation ends is not. Soon after, "we have not heard them derive a verb from it" reads "I have not heard" in [[root:Ebd|al-khalil-b-ahmad-al-farahidi-kitab-al-ain|the Kitāb al-ʿAyn entry for this root]], where much of the rest also appears, often closely worded, but with no statement of a shared sense. Take Q 43:81: "if the All-Merciful had a son, I would be the first of the *ʿābidīn*." Ibn Fāris files it under the second sense: it "has been interpreted" (*wa-fussira*) as "the first to be angered by this and to disdain it". The *ʿAyn* text on al-nuqta gives that reading too, but adds another in which *ʿābidīn* means worshippers. The *Maqāyīs* gives only the reading that serves its second *aṣl*.

## Reading it beside the Qur'an

The *Maqāyīs* shows a root as a family: which uses cluster, which ones Ibn Fāris could not place, and where he was unsure. It cannot settle a verse. An *aṣl* is his inference about how words are related, not a record of what a word meant in a particular sentence, and his Qur'anic citations are evidence chosen for his scheme. Weigh the verse's context and other dictionaries before letting a root sense decide a meaning.

Mind the dates. Ibn Fāris died in 1004–5, but the book passes on older material: verse by pre-Islamic poets such as Ṭarafa and al-Nābigha, and philologists of the eighth to tenth centuries. Sometimes he flags a later, narrower use himself. In [[root:fqh|ibn-faris-maqayis-al-lugha|ف ق ه]], *fiqh* is "every knowledge of a thing", and only "then" was it reserved for knowledge of the religious law. Where he flags nothing, that proves nothing.

When Hārūn edited it, from the single manuscript he could find, he had found no one besides Yāqūt who mentions the book, and he wrote that scholars had noticed it only recently.[^harun-ed|editor's introduction, pp. 39–40] It had been read, though. In several entries al-nuqta shows, al-Zabīdī's [[guide:taj-al-arus|Tāj al-ʿArūs]] cites "Ibn Fāris in the *Maqāyīs*". Under [[root:dlk|murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus|د ل ك]] it repeats, almost word for word, the reflection that closes [[root:dlk|ibn-faris-maqayis-al-lugha|his own entry]]: wherever dāl and lām are joined by a third letter, he finds, the word points to movement, to coming and going.`,
  onOurSite: `The stored text follows ʿAbd al-Salām Hārūn's edition: in the entries we compared, the wording is his, including his corrections to the single manuscript and the words he supplied in square brackets. His footnotes, which identify many of the poets Ibn Fāris quotes without naming, are not included. The full vowel marks, the verse references in square brackets, and the vowelled root heading that opens each entry, such as (كَفَرَ), are not in the edition's text as Shamela reproduces it.[^harun-ed][^hawramani]

The 1,323 roots shown cover every letter, but not every section. The section that opens each letter, on doubled roots, is missing, so there is no entry here for [[root:rbb|none|ر ب ب]] or [[root:rdd|none|ر د د]], though the book treats both.[^harun-ed|vol. 2, pp. 381, 386] Entries run from a single line to over a thousand words. In several letters the source copy runs the closing chapter on longer words into the root printed just before it. The end of [[root:kfr|ibn-faris-maqayis-al-lugha|ك ف ر]], from *kanfalīla* on, belongs to that chapter, not to the root. So does most of [[root:jvm|ibn-faris-maqayis-al-lugha|ج ث م]], where the chapter heading surfaces in the middle of a verse and the list breaks off.`,
  sources: [
    {
      id: 'harun-ed',
      kind: 'edition',
      citation: 'Ibn Fāris, *Muʿjam Maqāyīs al-Lugha*, ed. ʿAbd al-Salām Muḥammad Hārūn, 2nd ed., 6 vols (Cairo: Muṣṭafā al-Bābī al-Ḥalabī, 1969–72), with the editor’s introduction and the author’s preface; consulted in the page-matched text on al-Maktaba al-Shāmila.',
      url: 'https://shamela.ws/book/21710',
    },
    {
      id: 'sahibi',
      kind: 'primary',
      citation: 'Ibn Fāris, *al-Ṣāḥibī fī Fiqh al-Lugha al-ʿArabiyya wa-Masāʾilihā wa-Sunan al-ʿArab fī Kalāmihā* (Muḥammad ʿAlī Bayḍūn, 1997), “Bāb al-asbāb al-islāmiyya”, pp. 44–45; consulted on al-Maktaba al-Shāmila.',
      url: 'https://shamela.ws/book/9977/50',
    },
    {
      id: 'hawramani',
      kind: 'site',
      citation: 'The Arabic Lexicon (arabiclexicon.hawramani.com), “Ibn Fāris, Maqāyīs al-Lugha”, the source of the text al-nuqta displays; it does not name the edition it follows.',
      url: 'https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/',
    },
  ],
};

export default guide;
