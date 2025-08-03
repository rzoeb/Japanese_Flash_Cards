suitability_system_prompt = """
You are an AI assistant specialized in evaluating images to determine if they are suitable for generating Japanese language flashcards. You need to assess if the image contains characteristics that make it a good source for vocabulary and phrase extraction for language learning.

## Evaluation Criteria:
- **Presence of Japanese Text:** The image must contain Japanese text (Kanji, Hiragana, Katakana).
- **Presence of English Text (Optional but Recommended):**  Ideally, the image should also contain English text (translations, notes, explanations) to facilitate flashcard creation.
- **Clarity and Readability:** The text in the image should be clear, legible, and not overly distorted or low-resolution.

Your response will be automatically validated against a structured schema, so provide accurate assessments.
"""

suitability_user_prompt = """
Assess the attached image and determine if it is suitable for generating Japanese/English flashcards based on the criteria provided in the system prompt. Consider the presence of Japanese and English text, and the text clarity.

Provide your assessment with:
- is_suitable: "Yes" or "No"  
- reason: A brief explanation for your decision (max 1-2 sentences)
"""

flashcard_system_prompt = """
You are an AI assistant specialized in generating structured Anki flashcard data from Japanese vocabulary material. You are provided with both raw extracted text and an original image of a Japanese textbook page. Your task is to cross-reference the extracted text with the original image to correct any errors, fill in missing details, and ensure contextually accurate information.

## Strictly follow these rules:
- Use the original image as additional context when processing the extracted text.
- Extract all vocabulary and phrases accurately, correcting any discrepancies using the original image.
- Ensure each flashcard entry contains the word in Kanji (or Hiragana/Katakana if no Kanji exists), phonetic reading in Hiragana/Katakana, and English translation with usage notes.
- **Critical: Pay special attention to highlighted, emphasized, or colored words (e.g., in red, bold, or underlined) in the original image.** These highlighted words should be the main focus for flashcard creation. If a highlighted word appears within a sentence, create a flashcard for ONLY the highlighted word, and include the surrounding sentence context in the usage notes.
- The English meaning should correspond specifically to the highlighted/emphasized word, not the entire sentence.
- The surrounding words and sentence context should be included in the usage notes to provide learning context. The usage notes may be in either Japanese or English.
- Languages other than Japanese and English should be ignored.
- Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or if it should lead to the creation of a new flashcard.
- Pay attention to elements such as arrows, schematics, and layout cues to ensure accurate and contextually relevant flashcards.
- Customised 'Additional Instructions' may also be provided. If so, aim to follow them as closely as possible.

Your response will be automatically validated against a structured schema and converted to CSV format for Anki import. Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
"""

flashcard_system_prompt_kanji = """
You are an AI assistant specialized in generating structured Anki flashcard data for Kanji learning from Japanese textbook material. You are provided with both raw extracted text and an original image of a Japanese textbook page. Your task is to cross-reference the extracted text with the original image to create comprehensive Kanji flashcards.

## Strictly follow these rules:
- Use the original image as additional context when processing the extracted text.
- **Critical: Pay special attention to highlighted, emphasized, or colored Kanji characters (e.g., in red, bold, or underlined) in the original image.** These highlighted Kanji should be the main focus for flashcard creation.
- Extract all Kanji accurately, correcting any discrepancies using the original image.
- Each flashcard entry must contain:
  * **Kanji**: The individual Kanji character(s)
  * **Readings**: Both On-yomi (音読み) in Katakana and Kun-yomi (訓読み) in Hiragana, clearly separated. There is no need to duplicate Katakana readings in Hiragana and vice-versa.
  * **English Translation and Usage Notes**: Core meaning(s) and contextual usage information
  * **Example Words and Sentences**: Real usage examples showing the Kanji in context
- If a highlighted Kanji appears within a sentence or word, focus the flashcard on that specific Kanji, but include the surrounding context in the usage notes and examples.
- Languages other than Japanese and English should be ignored.
- Provide multiple readings when available (separate On-yomi and Kun-yomi clearly).
- Include stroke order or radicals information if visible in the source material.
- Pay attention to elements such as arrows, schematics, and layout cues to ensure accurate and contextually relevant flashcards.
- Customised 'Additional Instructions' may also be provided. If so, aim to follow them as closely as possible.

Your response will be automatically validated against a structured schema and converted to CSV format for Anki import. Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
"""

flashcard_system_prompt_grammar = """
You are an AI assistant specialized in generating structured Anki flashcard data for Japanese grammar learning from Japanese textbook material. You are provided with both raw extracted text and an original image of a Japanese textbook page. Your task is to cross-reference the extracted text with the original image to create comprehensive grammar flashcards.

## Strictly follow these rules:
- Use the original image as additional context when processing the extracted text.
- **Critical: Pay special attention to highlighted, emphasized, or colored grammar points (e.g., in red, bold, or underlined) in the original image.** These highlighted grammar patterns should be the main focus for flashcard creation.
- Extract all grammar points accurately, correcting any discrepancies using the original image.
- Each flashcard entry must contain:
  * **Grammar Point**: The grammar pattern in Kanji or Hiragana/Katakana (e.g., ～ている, ～たら, ～ばかり)
  * **English Explanation and Notes**: Clear explanation of the grammar usage, meaning, and any important contextual notes
  * **Example Sentences**: Real Japanese sentences demonstrating the grammar point in context
- If a highlighted grammar point appears within explanatory text, focus the flashcard on that specific grammar pattern, but include surrounding context in the explanation and notes.
- Languages other than Japanese and English should be ignored.
- Include nuances, formality levels, and usage restrictions when available in the source material.
- Pay attention to elements such as arrows, diagrams, conjugation tables, and layout cues to ensure accurate and contextually relevant flashcards.
- Focus on grammar structures, particles, conjugations, and sentence patterns rather than individual vocabulary words.
- Include information about when and how to use the grammar point (formal/informal situations, restrictions, etc.).
- **Important: When a grammar point has multiple form combinations (e.g., V-ます/V-ない + pattern, い-A + pattern, な-A + pattern, N + pattern), combine ALL variations into a single flashcard entry separated by "|" rather than creating separate entries for each form.**
- Customised 'Additional Instructions' may also be provided. If so, aim to follow them as closely as possible.

Your response will be automatically validated against a structured schema and converted to CSV format for Anki import. Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
"""

flashcard_user_prompt_example_1 = """
Extract Japanese vocabulary from the provided extracted text and cross-reference it with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as arrows, schematics, or layout cues) to correct any errors in the extracted text. Then, generate Anki flashcards in CSV format with the following columns: **Kanji, Furigana, English_Translation_and_Notes.**

## Instructions:
- Ensure that all Japanese words have their correct **Kanji representation.**
- If a word does not have Kanji, use its Hiragana/Katakana form in the **Kanji** column.
- Include **Furigana readings** in a separate column.
- Provide the **English translation**, along with any **usage notes** from the source. The usage notes may be in either Japanese or English. Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or be used to create a new flashcard. In either case, the usage notes must always be placed in the **English_Translation_and_Notes** column.
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
- The output must **strictly** adhere to CSV format, with no extra explanations or irrelevant text.

## Response Format:
Return a structured response with the following fields:
- kanji: Word in Kanji or Hiragana/Katakana
- furigana: Phonetic reading in Hiragana
- english_translation_and_notes: English translation with usage notes

The English meaning should correspond specifically to the highlighted/emphasized word, not the entire sentence. The surrounding words and sentence context should be included in the usage notes to provide learning context.

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the CSV output.

---EXTRACTED TEXT STARTS HERE---

III. Useful Words and 
                             Information 
             ま つ      め い し ょ 

              祭 り と    名 所 
                                 Festivals and 
                                                Places of Note 

         ろ く お ん じ き ん か く じ き ん か く 
          鹿 苑 寺 ( 金 閣 寺 ) 金 閣 

                                     ふ じ さ ん 
                                     富 士 山 

  ひ め じ じ ょ う                                                      と う し ょ う ぐ う 
  姫 路 城                                                            東 照 宮 

                    ぎ お ん ま つ り 
                   祇 園 祭 

                                                                  こ う き ょ 
                                                                  皇 居 
げ ん ば く 
                                                                                79 
 原 爆 ド ー ム 
                                                日 光 

                                                 東 京 

                                   京 都                                          12 
                               大 阪 
                         路         奈 良 
                   広 島 

                      in the 

                                 00                           か ん だ ま つ り 
                                 0000                          神 田 祭 
                              0000 0000 
                                                 だ い ぶ つ 
                                         と う だ い じ 
                                                 大 仏 
                                          東 大 寺 · 

                         て ん じ ん ま つ り 
                         天 神 祭 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_example_1 = """
"祭りと名所","まつりとめいしょ","Festivals and Places of Note"
"祭り","まつり","festival"
"名所","めいしょ","place of note; famous place"
"鹿苑寺","ろくおんじ","Rokuon-ji (formal name of Kinkaku-ji in Kyoto. Also known as the Temple of the Golden Pavilion)"
"金閣寺","きんかくじ","Kinkaku-ji (Temple of the Golden Pavilion in Kyoto)"
"金閣","きんかく","Kinkaku (the Golden Pavilion building in Kyoto)"
"富士山","ふじさん","Mount Fuji, Japan’s tallest mountain"
"姫路城","ひめじじょう","Himeji Castle, a UNESCO World Heritage Site"
"東照宮","とうしょうぐう","Tōshōgū Shrine, a famous Shinto shrine in Nikkō"
"祇園祭","ぎおんまつり","Gion Festival, a major Kyoto festival held in July"
"皇居","こうきょ","Imperial Palace in Tokyo"
"原爆ドーム","げんばくドーム","Atomic Bomb Dome in Hiroshima, a memorial for the 1945 bombing"
"日光","にっこう","Nikkō, a historic city famous for its shrines and nature"
"東京","とうきょう","Tokyo, the capital city of Japan"
"京都","きょうと","Kyoto"
"大阪","おおさか","Osaka"
"奈良","なら","Nara, an ancient capital of Japan"
"広島","ひろしま","Hiroshima"
"神田祭","かんだまつり","Kanda Festival, one of Tokyo’s most famous Shinto festivals"
"大仏","だいぶつ","Great Buddha in Nara"
"東大寺","とうだいじ","Tōdaiji Temple in Nara"
"天神祭","てんじんまつり","Tenjin Festival, a famous festival in Osaka"
"""

flashcard_user_prompt_example_2 = """
Extract Japanese vocabulary from the provided extracted text and cross-reference it with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as arrows, schematics, or layout cues) to correct any errors in the extracted text. Then, generate Anki flashcards in CSV format with the following columns: **Kanji, Furigana, English_Translation_and_Notes.**

## Instructions:
- Ensure that all Japanese words have their correct **Kanji representation.**
- If a word does not have Kanji, use its Hiragana/Katakana form in the **Kanji** column.
- Include **Furigana readings** in a separate column.
- Provide the **English translation**, along with any **usage notes** from the source. The usage notes may be in either Japanese or English. Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or be used to create a new flashcard. In either case, the usage notes must always be placed in the **English_Translation_and_Notes** column.
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
- The output must **strictly** adhere to CSV format, with no extra explanations or irrelevant text.

## Response Format:
Return a structured response with the following fields:
- kanji: Word in Kanji or Hiragana/Katakana
- furigana: Phonetic reading in Hiragana
- english_translation_and_notes: English translation with usage notes

The English meaning should correspond specifically to the highlighted/emphasized word, not the entire sentence. The surrounding words and sentence context should be included in the usage notes to provide learning context.

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the CSV output.

---EXTRACTED TEXT STARTS HERE---

                             Lesson          1 

ど の よ う に                            how 

 迷 う [ 道 に ~]    ま よ う [ み ち に ~]    lose [one's way] 

先 輩              せ ん ぱ い             senior (student, colleague, etc.) 

 ま る で                               just (as in X is just like Y') 

 明 る い           あ か る い             cheerful [personality] 

   [ 性 格 が ~]      [ せ い か く が ~] 
                                             は は お や 
 父 親             ち ち お や             father (cf. 母 親 :mother) 

 湖               み ず う み             lake 

 目 指 す           め ざ す               aim at, have one's eye on 
 命               い の ち               life 

 お せ ち 料 理       お せ ち り ょ う り       traditional Japanese food for the New Year 

 初 詣 で           は つ も う で           traditional practice of visiting a shrine or 

                                      temple during the New Year to pray for 

                                      happiness 
 畳               た た み               tatami mat (thick straw mat 
                                                            used for flooring 
                                      in traditional Japanese rooms) 
 座 布 団           ざ ぶ と ん            square floor cushion for sitting or 
                                                                kneeling on 
 床               ゆ か                floor 

 正 座             せ い ざ              formal kneeling position, with buttocks on 

                                      heels, body upright, and hands in lap 
 お じ ぎ                              bow (greeting) 

 作 家             さ っ か              writer, author 

 ~ 中 [ 留 守 ~]    ~ ち ゅ う [ る す ~]   while [while out] 
 い っ ぱ い                            full, crowded 

 ど ん な に                            however, no matter how 

 立 派 [ な ]       り っ ぱ [ な ]        wonderful, grand 

 欠 点             け っ て ん            failing, shortcoming 

~ 過 ぎ            ~ す ぎ              past, after, gone 

似 合 う            に あ う              suit, look good in 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_example_2 = """
"どのように","どのように","how"
"迷う [道に～]","まよう [みちに～]","lose [one's way]"
"先輩","せんぱい","senior (student, colleague, etc.)"
"まるで","まるで","just (as in X is just like Y')"
"明るい [性格が～]","あかるい [せいかくが～]","cheerful [personality]"
"父親","ちちおや","father (cf. 母親: mother)"
"湖","みずうみ","lake"
"目指す","めざす","aim at, have one's eye on"
"命","いのち","life"
"おせち料理","おせちりょうり","traditional Japanese food for the New Year"
"初詣で","はつもうで","traditional practice of visiting a shrine or temple during the New Year to pray for happiness"
"畳","たたみ","tatami mat (thick straw mat used for flooring in traditional Japanese rooms)"
"座布団","ざぶとん","square floor cushion for sitting or kneeling on"
"床","ゆか","floor"
"正座","せいざ","formal kneeling position, with buttocks on heels, body upright, and hands in lap"
"おじぎ","おじぎ","bow (greeting)"
"作家","さっか","writer, author"
"~中 [留守~]","~ちゅう [るす~]","while [while out]"
"いっぱい","いっぱい","full, crowded"
"どんなに","どんなに","however, no matter how"
"立派[な]","りっぱ[な]","wonderful, grand"
"欠点","けってん","failing, shortcoming"
"~過ぎ","~すぎ","past, after, gone"
"似合う","にあう","suit, look good in"
"""

flashcard_user_prompt_example_3 = """
Extract Japanese vocabulary from the provided extracted text and cross-reference it with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as arrows, schematics, or layout cues) to correct any errors in the extracted text. Then, generate Anki flashcards in CSV format with the following columns: **Kanji, Furigana, English_Translation_and_Notes.**

## Instructions:
- Ensure that all Japanese words have their correct **Kanji representation.**
- If a word does not have Kanji, use its Hiragana/Katakana form in the **Kanji** column.
- Include **Furigana readings** in a separate column.
- Provide the **English translation**, along with any **usage notes** from the source. The usage notes may be in either Japanese or English. Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or be used to create a new flashcard. In either case, the usage notes must always be placed in the **English_Translation_and_Notes** column.
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
- The output must **strictly** adhere to CSV format, with no extra explanations or irrelevant text.

## Response Format:
Return a structured response with the following fields:
- kanji: Word in Kanji or Hiragana/Katakana
- furigana: Phonetic reading in Hiragana
- english_translation_and_notes: English translation with usage notes

The English meaning should correspond specifically to the highlighted/emphasized word, not the entire sentence. The surrounding words and sentence context should be included in the usage notes to provide learning context.

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the CSV output.

---EXTRACTED TEXT STARTS HERE---

魚 を 捕 ま え る           catch fish 捕 鱼 물 고 기 를 잡 다 →(~ が ) 捕 ま る              히 다 
    つ か                                             つ か          be caught 捕 捉 잡 

魚 を つ る               fish 钓 鱼 물 고 기 를 낚 다   → 棚 を つ る           put up a shelf 
                                               た な               挂 吊 板 선 반 을 매 달 다 
                                                                 get conned 
                      catch fish with a net → 詐 欺 に 引 っ か か る 
                                                さ ぎ   ひ          被 诈 骗 사 기 에 걸 리 다 
魚 が 網 に 引 っ か か る     鱼 被 网 子 兜 住 了 
    あ み ひ                                                       hook 
                      물 고 기 가 망 에 걸 리 다      →(~ を ) 引 ひ っ か け る 
                                                                挂 ~ , 欺 骗 ~ (~ 을 ) 걸 다 
                                                                pedal a bicycle 蹬 自 行 车 
ボ ー ト を こ ぐ           row a boat 划 船 보 트 를 젓 다 → 自 転 車 を こ ぐ 
                                                                자 전 거 페 달 을 밟 다 
                      a boat is tipped over                     overturn ... 
ボ ー ト が ひ っ く り 返 る                          →(~ を ) ひ っ く り 返 す 
                か え   船 翻 了 보 트 가 전 복 하 다                   か え 把 …… 弄 翻 (~ 을 ) 뒤 집 다 
                      the whereabouts of the boat               being missing 
ボ ー ト の 行 方                                  → 行 方 不 明 
         ゆ く え        船 的 去 处 보 트 의 행 방         ゆ く え ふ め い     下 落 不 明 행 방 불 명 
                                                      C 
                                                       近 づ く    a shark comes close 
                      take a boat into the shore        ち か 
船 を 岸 に 近 づ け る                              → サ メ が            鲨 鱼 靠 近 了 
ふ ね き し ち か           把 船 靠 岸 배 를 물 가 에 대 다            近 寄 る 
                                                        ち か よ   상 어 가 가 까 이 오 다 

あ ち こ ち / あ ち ら こ ち ら             here and there 四 处 여 기 저 기 
                                  tempting bait 看 上 去 很 美 味 的 饲 料 
 う ま そ う な (= お い し そ う な ) え さ   맛 있 을 것 같 은 먹 이                   ま ず そ う 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_example_3 = """
"捕まえる","つかまえる","catch, capture. Context: 「魚を捕まえる」(catch fish). Intransitive pair note: 「(~が)捕まる」= be caught."
"捕まる","つかまる","be caught, be captured. Usage note: arrow from 「魚を捕まえる」→「(~が)捕まる」."
"釣る","つる","to fish, angle. Context: 「魚を釣る」. Contrast with 「吊る」(to hang) as in 「棚を吊る」."
"吊る","つる","to hang, suspend. Context: 「棚を吊る」(put up a shelf)."
"引っかかる","ひっかかる","to get caught, be snagged, get conned. Context: 「魚が網に引っかかる」; also 「詐欺に引っかかる」(get conned)."
"引っかける","ひっかける","to hook, hang, trick (transitive). Pattern: 「(~を)引っかける」."
"漕ぐ","こぐ","to row, to pedal. Context: 「ボートを漕ぐ」(row a boat), 「自転車を漕ぐ」(pedal a bicycle)."
"ひっくり返る","ひっくりかえる","to capsize, be overturned (intransitive). Context: 「ボートがひっくり返る」(a boat is tipped over)."
"ひっくり返す","ひっくりかえす","to overturn, flip over (transitive). Pattern: 「(~を)ひっくり返す」."
"行方","ゆくえ","whereabouts. Context: 「ボートの行方」(the whereabouts of the boat)."
"行方不明","ゆくえふめい","missing, whereabouts unknown. Note: arrow from 「ボートの行方」→「行方不明」."
"近づける","ちかづける","to bring close, move nearer (transitive). Context: 「船を岸に近づける」(take a boat into the shore)."
"近づく","ちかづく","to approach, come close (intransitive). Context: 「サメが近づく」(a shark comes close)."
"近寄る","ちかよる","to draw near, approach (synonym of 近づく). Appears with 「サメが近寄る」 as an alternative."
"あちこち／あちらこちら","あちこち／あちらこちら","here and there. Listed as a pair of variants."
"うまそうな","うまそうな","looks tasty, appetizing-looking. Note: 「(=おいしそうな)」."
"餌","えさ","bait, feed. Context: 「うまそうな餌」(tempting bait); contrast arrow indicates 「↔ まずそう」(looks unappetizing)."
"""

flashcard_user_prompt_actual = """
Extract Japanese vocabulary from the provided extracted text and cross-reference it with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as arrows, schematics, or layout cues) to correct any errors in the extracted text. Then, generate structured Anki vocabulary flashcard data.

## Critical Instructions:
- **Pay special attention to highlighted, emphasized, or colored words (e.g., in red, bold, or underlined) in the original image.** These highlighted words should be the main focus for flashcard creation.
- If a highlighted word appears within a sentence, create a flashcard for ONLY the highlighted word, and include the surrounding sentence context in the usage notes.
- Ensure that all Japanese words have their correct **Kanji representation.**
- If a word does not have Kanji, use its Hiragana/Katakana form in the **kanji** field.
- Include **Furigana readings** in the **furigana** field (phonetic reading in Hiragana/Katakana).
- Provide the **English translation**, along with any **usage notes** from the source in the **english_translation_and_notes** field. The usage notes may be in either Japanese or English.
- Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or be used to create a new flashcard.
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.
- Languages other than Japanese and English should be ignored.
- Pay attention to elements such as arrows, schematics, and layout cues to ensure accurate and contextually relevant flashcards.

{additional_instructions}

## Response Format:
Return a structured response with the following fields:
- kanji: Word in Kanji or Hiragana/Katakana
- furigana: Phonetic reading in Hiragana
- english_translation_and_notes: English translation with usage notes

The English meaning should correspond specifically to the highlighted/emphasized word, not the entire sentence. The surrounding words and sentence context should be included in the usage notes to provide learning context.

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

{extracted_text}

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_user_prompt_kanji_example_1 = """
Extract Kanji characters from the provided extracted text and cross-reference them with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as highlighting, emphasis, or layout cues) to identify the target Kanji for flashcard creation. Then, generate structured Anki Kanji flashcard data.

## Instructions:
- **Focus on highlighted, emphasized, or colored Kanji** in the original image as the primary targets for flashcard creation.
- For each target Kanji, provide:
  * **kanji**: The individual Kanji character(s)
  * **readings**: Both On-yomi in Katakana and Kun-yomi in Hiragana (format: "オン、音読み | くん、くんよみ"). There is no need to duplicate Katakana readings in Hiragana and vice-versa.
  * **english_translation_and_notes**: Core meanings and contextual usage information
  * **example_words_and_sentences**: Real usage examples showing the Kanji in practical contexts
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- If a Kanji appears in multiple contexts, include all relevant information.
- Ignore languages other than Japanese and English.
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.

## Response Format:
Return a structured response with the following fields:
- kanji: The Kanji character(s)
- readings: On-yomi and Kun-yomi readings (separated by " | ")
- english_translation_and_notes: English meanings and usage notes
- example_words_and_sentences: Example words and sentences using the Kanji

## Example Output:
"学","ガク | まな","study, learning; to learn","学校 (がっこう) - school; 学生 (がくせい) - student; 学ぶ (まなぶ) - to learn; 数学を学んでいます - I am studying mathematics"
"時","ジ | とき","time, hour; when","時間 (じかん) - time; 何時 (なんじ) - what time; 時々 (ときどき) - sometimes; その時、雨が降っていました - At that time, it was raining"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

                            fall 滚 下 전 락                  failing/repeating a course 
          ラ ク    転 落        a                    落 第 
                                                                            第 (p.25) 
                 て ん ら く                         ら く だ い 不 及 格 낙 제 
     12 画 お ち る 
落 
          お と す 落 ち る       fall 落 下 떨 어 지 다     落 と す                뜨 리 다 
                 お                               お        drop 使 落 下 떨 어 

          セ キ    落 石        falling rocks 落 石 낙 석 磁 石     a magnet / compass 
                 ら く せ き                         じ し ゃ く 磁 铁 、 指 南 针 자 석 , 나 침 반 
      5 画 シ ャ ク 
石 
          い し    石          a stone 石 头 돌 
                 い し 
                                                 不 動    常 表 团 
          ヒ      飛 行 場      an airport 机 场 비 행 장 
                 ひ こ う じ ょ う 
      9 画 と ー ぶ 
飛                                                飛 び 出 す run out suddenly 
          と ー ば す 飛 と ぶ     fly 飞 行 날 다 
                                                 と   だ    跳 出 뛰 어 나 가 다 

                 駐 車 場      a parking lot 停 车 场 주 차 장 駐 車 parking 停 车 주 차 
                 ち ゅ う し ゃ じ ょ う                 ち ゅ う し ゃ 
      15 画 チ ュ ウ 
駐 

                            round to the nearest (e.g. decimal place) 
                 四 捨 五 入 
           シ ャ    し し ゃ ご に ゅ う 四 舍 五 入 반 올 림 
      11 画 
捨          す ー て る 捨 て る    throw away 抛 弃 버 리 다 
                  す 

                 遊 泳        swimming 游 泳 유 영 
           ユ ウ   ゆ う え い 
      12 画 
 遊         あ そ ー ぶ 遊 ぶ      play 玩 놀 다              s 
                 あ そ                                        茶 

                 水 泳        swimming 游 泳 수 영 
           エ イ   す い え い 
       8 画 
 泳         お よ ー ぐ 泳 ぐ      swim 游 泳 수 영 하 다 
                 お よ 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_kanji_example_1 = """
"落","ラク | おちる・おとす","fall, drop; also used for academic failure (落第). Notes: intransitive 落ちる=to fall, transitive 落とす=to drop.","落ちる（おちる）- to fall; 落とす（おとす）- to drop; 落石（らくせき）- falling rocks; 落第（らくだい）- failing/repeating a course"
"石","セキ・シャク | いし","stone, rock. On-yomi シャク appears in compounds like 磁石.","石（いし）- a stone; 落石（らくせき）- falling rocks; 磁石（じしゃく）- magnet/compass"
"飛","ヒ | とぶ・とばす","fly, jump, leap; can be intransitive/transitive pair (飛ぶ／飛ばす).","飛ぶ（とぶ）- to fly; 飛ばす（とばす）- to let fly/skip; 飛行場（ひこうじょう）- airport; 飛び出す（とびだす）- to dash out/run out suddenly"
"駐","チュウ | なし","to park, stop (for vehicles); used mainly in compounds.","駐車（ちゅうしゃ）- parking; 駐車場（ちゅうしゃじょう）- parking lot"
"捨","シャ | すてる","to throw away, discard; appears in the rounding term 四捨五入.","捨てる（すてる）- to throw away; 四捨五入（ししゃごにゅう）- round to the nearest (e.g., decimal place)"
"遊","ユウ | あそぶ","to play, amuse; leisure-related compounds.","遊ぶ（あそぶ）- to play; 遊泳（ゆうえい）- swimming"
"泳","エイ | およぐ","to swim; water-related compounds.","泳ぐ（およぐ）- to swim; 水泳（すいえい）- swimming"
"""

flashcard_user_prompt_actual_kanji = """
Extract Kanji characters from the provided extracted text and cross-reference them with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as highlighting, emphasis, or layout cues) to identify the target Kanji for flashcard creation. Then, generate structured Anki Kanji flashcard data.

## Instructions:
- **Focus on highlighted, emphasized, or colored Kanji** in the original image as the primary targets for flashcard creation.
- For each target Kanji, provide:
  * **kanji**: The individual Kanji character(s)
  * **readings**: Both On-yomi in Katakana and Kun-yomi in Hiragana (format: "オン、音読み | くん、くんよみ"). There is no need to duplicate Katakana readings in Hiragana and vice-versa.
  * **english_translation_and_notes**: Core meanings and contextual usage information
  * **example_words_and_sentences**: Real usage examples showing the Kanji in practical contexts
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- If a Kanji appears in multiple contexts, include all relevant information.
- Ignore languages other than Japanese and English.
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.

{additional_instructions}

## Response Format:
Return a structured response with the following fields:
- kanji: The Kanji character(s)
- readings: On-yomi and Kun-yomi readings (separated by " | ")
- english_translation_and_notes: English meanings and usage notes
- example_words_and_sentences: Example words and sentences using the Kanji

## Example Output:
"学","ガク | まな","study, learning; to learn","学校 (がっこう) - school; 学生 (がくせい) - student; 学ぶ (まなぶ) - to learn; 数学を学んでいます - I am studying mathematics"
"時","ジ | とき","time, hour; when","時間 (じかん) - time; 何時 (なんじ) - what time; 時々 (ときどき) - sometimes; その時、雨が降っていました - At that time, it was raining"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

{extracted_text}

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_user_prompt_grammar_example_1 = """
Extract Japanese grammar points from the provided extracted text and cross-reference them with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as highlighting, emphasis, or layout cues) to identify the target grammar patterns for flashcard creation. Then, generate structured Anki grammar flashcard data.

## Critical Instructions:
- **Pay special attention to highlighted, emphasized, or colored grammar points (e.g., in red, bold, or underlined) in the original image.** These highlighted grammar patterns should be the main focus for flashcard creation.
- Focus on grammar structures, particles, conjugations, and sentence patterns rather than individual vocabulary words.
- For each target grammar point, provide:
  * **grammar_point**: The grammar pattern in Kanji or Hiragana/Katakana (e.g., ～ている, ～たら, ～ばかり)
  * **english_explanation_and_notes**: Clear explanation of the grammar usage, meaning, formality level, and any important contextual notes
  * **example_sentences**: Real Japanese sentences demonstrating the grammar point in practical contexts
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Include nuances, formality levels, and usage restrictions when available in the source material.
- Pay attention to elements such as arrows, diagrams, conjugation tables, and layout cues to ensure accurate and contextually relevant flashcards.
- **Critical: If a grammar point can attach to multiple word types (verbs, adjectives, nouns), combine ALL form variations into a single flashcard entry separated by "|" in the grammar_point field. Do NOT create separate flashcard entries for each form combination.**
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.
- Languages other than Japanese and English should be ignored.

## Response Format:
Return a structured response with the following fields:
- grammar_point: The grammar pattern in Kanji or Hiragana/Katakana
- english_explanation_and_notes: English explanation of the grammar point with usage notes
- example_sentences: Example sentences using the grammar point (in Japanese)

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"V-ます/V-ない + ながら | い-A + ながら | な-A + ながら | N + ながら(も)","Grammar pattern expressing simultaneous actions or contrasting situations. When you want to say 'this is the situation, but...' or 'while doing X, Y happens'. Can attach to verb stems, adjectives, and nouns.","彼とは同じ寮に住んでいながら、ほとんど話をしたことがなかった。(Even though we live in the same dormitory, we hardly ever talked.) | 彼は若いながらも、立派なプロジェクトリーダーだ。(Even though he is young, he is an excellent project leader.) | このICレコーダーは小型でありながら、連続24時間の録音が可能だ。(This IC recorder is small, yet it can record continuously for 24 hours.)"
"V-て + います","Present progressive/continuous tense and habitual action. Expresses ongoing actions, current states, or repeated actions.","今、勉強しています。(I am studying now.) | 毎日テレビを見ています。(I watch TV every day.) | 田中さんは結婚しています。(Mr. Tanaka is married.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

         ざ ん ね ん 
   15    残 念 な が ら 

 ど う 使 う ? 
                じ ょ う た い 
「 ~ な が ら 」 は 、 「 ~ の 状 態 だ が 、 け れ ど も 」 と 言 い た い と き に 使 う 。 
Use " ~ な が ら " when you want to say "this is the situation, but ... " 

V- ま す /V- な い 
い A 
                     + な が ら ( も ) 
な A 
N 
* 「 な A/N で あ り + な が ら 」 の 形 も あ る 。 

           り ょ う 
1 彼 と は 同 じ 寮 に 住 ん で い な が ら 、 ほ と ん ど 話 を し た こ と が な か っ た 。 

2 留 学 生 た ち は 、 難 し い 言 葉 は わ か ら な い な が ら 、 日 本 人 の ボ ラ ン テ ィ ア と 楽 し そ う に お 

  し ゃ べ り し て い る 。 
                  り っ ぱ 
3 彼 は 若 い な が ら も 、 立 派 な プ ロ ジ ェ ク ト リ ー ダ ー だ 。 
      じ あ い          ゆ う し ょ う か 
4 練 習 試 合 な が ら 、 去 年 の 優 勝 チ ー ム に 勝 っ た の は 大 き な 自 信 に な る 。 
                   こ が た          れ ん ぞ く   ろ く お ん か の う 
5 こ の IC レ コ ー ダ ー は 小 型 で あ り な が ら 、 連 続 24 時 間 の 録 音 が 可 能 だ 。 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_grammar_example_1 = """
"V-ます/V-ない + ながら | い-Adj + ながら | な-Adj + ながら(も) | N + ながら(も) | な-Adj/N + であり + ながら","Concessive pattern meaning ""although/though; this is the situation, but …"". Attaches to verb ます-stem (e.g., 知りながら) or negative plain form (わからないながら), to い/な adjectives, and to nouns. 「ながらも」 adds stronger contrast/emphasis. With 「でありながら」 after N/な-Adj it sounds more formal/written. Note: this entry is the contrastive ながら, not the simultaneous ""while \~ing"" use.","彼とは同じ寮に住んでいながら、ほとんど話をしたことがなかった。| 留学生たちは、難しい言葉はわからないながら、日本人のボランティアと楽しそうにおしゃべりしている。| 彼は若いながらも、立派なプロジェクトリーダーだ。| 練習試合ながら、去年の優勝チームに勝ったのは大きな自信になる。| このICレコーダーは小型でありながら、連続24時間の録音が可能だ。"
"""

flashcard_user_prompt_grammar_example_2 = """
Extract Japanese grammar points from the provided extracted text and cross-reference them with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as highlighting, emphasis, or layout cues) to identify the target grammar patterns for flashcard creation. Then, generate structured Anki grammar flashcard data.

## Critical Instructions:
- **Pay special attention to highlighted, emphasized, or colored grammar points (e.g., in red, bold, or underlined) in the original image.** These highlighted grammar patterns should be the main focus for flashcard creation.
- Focus on grammar structures, particles, conjugations, and sentence patterns rather than individual vocabulary words.
- For each target grammar point, provide:
  * **grammar_point**: The grammar pattern in Kanji or Hiragana/Katakana (e.g., ～ている, ～たら, ～ばかり)
  * **english_explanation_and_notes**: Clear explanation of the grammar usage, meaning, formality level, and any important contextual notes
  * **example_sentences**: Real Japanese sentences demonstrating the grammar point in practical contexts
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Include nuances, formality levels, and usage restrictions when available in the source material.
- Pay attention to elements such as arrows, diagrams, conjugation tables, and layout cues to ensure accurate and contextually relevant flashcards.
- **Critical: If a grammar point can attach to multiple word types (verbs, adjectives, nouns), combine ALL form variations into a single flashcard entry separated by "|" in the grammar_point field. Do NOT create separate flashcard entries for each form combination.**
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.
- Languages other than Japanese and English should be ignored.

## Response Format:
Return a structured response with the following fields:
- grammar_point: The grammar pattern in Kanji or Hiragana/Katakana
- english_explanation_and_notes: English explanation of the grammar point with usage notes
- example_sentences: Example sentences using the grammar point (in Japanese)

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"V-ます/V-ない + ながら | い-A + ながら | な-A + ながら | N + ながら(も)","Grammar pattern expressing simultaneous actions or contrasting situations. When you want to say 'this is the situation, but...' or 'while doing X, Y happens'. Can attach to verb stems, adjectives, and nouns.","彼とは同じ寮に住んでいながら、ほとんど話をしたことがなかった。(Even though we live in the same dormitory, we hardly ever talked.) | 彼は若いながらも、立派なプロジェクトリーダーだ。(Even though he is young, he is an excellent project leader.) | このICレコーダーは小型でありながら、連続24時間の録音が可能だ。(This IC recorder is small, yet it can record continuously for 24 hours.)"
"V-て + います","Present progressive/continuous tense and habitual action. Expresses ongoing actions, current states, or repeated actions.","今、勉強しています。(I am studying now.) | 毎日テレビを見ています。(I watch TV every day.) | 田中さんは結婚しています。(Mr. Tanaka is married.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

2. ~ て も か ま わ な い { 

    V て -form 

    い A        → く て 
                          + も か ま わ な い 
     な A 
             + で 
     N    } 

     「 ~ て も か ま わ な い 」 indicates allowing or giving permission to do something. In an 

     interrogative sentence, it is used for asking permission to do something. Although it 

     means the same as 「 ~ て も い い 」 , it is more formal: 
                す わ 
      1   こ こ に 座 っ て も か ま い ま せ ん か 。 May I sit here, please? 
          ま    あ 
      2 間 に 合 わ な か っ た ら 、 あ し た で も か ま い ま せ ん 。 

          If you run out of time today, tomorrow will be acceptable. 
                                       し ゃ し ん と 
      Ref: 「 ~ て も い い (permission) 」 : 写 真 を 撮 っ て も い い で す 。 
                                                        ( 『 み ん な の 日 本 語 初 級 』 Lesson 15) 
<<<

---EXTRACTED TEXT ENDS HERE---
"""

flashcard_answer_grammar_example_2 = """
"V-て + もかまわない | い-Adj(～くて) + もかまわない | な-Adj/N + で + もかまわない","Formal pattern meaning ""it doesn’t matter (even if) ~ / it’s acceptable to ~"" and used to allow or give permission. In interrogatives it asks for permission (e.g., ～てもかまいませんか). Semantically similar to 「～てもいい」 but more formal/polite. Attach via verb て-form, い-adjectives with ～くて, and な-adjectives/nouns + で.","ここに座ってもかまいませんか。| 間に合わなかったら、あしたでもかまいません。| （参考）写真を撮ってもいいです。"
"""

flashcard_user_prompt_actual_grammar = """
Extract Japanese grammar points from the provided extracted text and cross-reference them with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as highlighting, emphasis, or layout cues) to identify the target grammar patterns for flashcard creation. Then, generate structured Anki grammar flashcard data.

## Critical Instructions:
- **Pay special attention to highlighted, emphasized, or colored grammar points (e.g., in red, bold, or underlined) in the original image.** These highlighted grammar patterns should be the main focus for flashcard creation.
- Focus on grammar structures, particles, conjugations, and sentence patterns rather than individual vocabulary words.
- For each target grammar point, provide:
  * **grammar_point**: The grammar pattern in Kanji or Hiragana/Katakana (e.g., ～ている, ～たら, ～ばかり)
  * **english_explanation_and_notes**: Clear explanation of the grammar usage, meaning, formality level, and any important contextual notes
  * **example_sentences**: Real Japanese sentences demonstrating the grammar point in practical contexts
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Include nuances, formality levels, and usage restrictions when available in the source material.
- Pay attention to elements such as arrows, diagrams, conjugation tables, and layout cues to ensure accurate and contextually relevant flashcards.
- **Critical: If a grammar point can attach to multiple word types (verbs, adjectives, nouns), combine ALL form variations into a single flashcard entry separated by "|" in the grammar_point field. Do NOT create separate flashcard entries for each form combination.**
- Your response will be automatically validated against a structured schema and converted to CSV format for Anki import.
- Languages other than Japanese and English should be ignored.

{additional_instructions}

## Response Format:
Return a structured response with the following fields:
- grammar_point: The grammar pattern in Kanji or Hiragana/Katakana
- english_explanation_and_notes: English explanation of the grammar point with usage notes
- example_sentences: Example sentences using the grammar point (in Japanese)

Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.

## Example Output:
"V-ます/V-ない + ながら | い-A + ながら | な-A + ながら | N + ながら(も)","Grammar pattern expressing simultaneous actions or contrasting situations. When you want to say 'this is the situation, but...' or 'while doing X, Y happens'. Can attach to verb stems, adjectives, and nouns.","彼とは同じ寮に住んでいながら、ほとんど話をしたことがなかった。(Even though we live in the same dormitory, we hardly ever talked.) | 彼は若いながらも、立派なプロジェクトリーダーだ。(Even though he is young, he is an excellent project leader.) | このICレコーダーは小型でありながら、連続24時間の録音が可能だ。(This IC recorder is small, yet it can record continuously for 24 hours.)"
"V-て + います","Present progressive/continuous tense and habitual action. Expresses ongoing actions, current states, or repeated actions.","今、勉強しています。(I am studying now.) | 毎日テレビを見ています。(I watch TV every day.) | 田中さんは結婚しています。(Mr. Tanaka is married.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the structured response.

---EXTRACTED TEXT STARTS HERE---

{extracted_text}

---EXTRACTED TEXT ENDS HERE---
"""