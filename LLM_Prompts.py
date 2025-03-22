suitability_system_prompt = """
You are an AI assistant specialized in evaluating images to determine if they are suitable for generating Japanese language flashcards. You need to assess if the image contains characteristics that make it a good source for vocabulary and phrase extraction for language learning.

## Evaluation Criteria:
- **Presence of Japanese Text:** The image must contain Japanese text (Kanji, Hiragana, Katakana).
- **Presence of English Text (Optional but Recommended):**  Ideally, the image should also contain English text (translations, notes, explanations) to facilitate flashcard creation.
- **Clarity and Readability:** The text in the image should be clear, legible, and not overly distorted or low-resolution.

## Output Format:
You must strictly output your answer in JSON format according to the following schema:

{
  "is_suitable": "Yes" or "No",
  "reason": "A brief explanation for your decision (max 1-2 sentences)"
}

**Do not output any text outside of the JSON structure.**
"""

suitability_user_prompt = """
Assess the attached image and determine if it is suitable for generating Japanese/English flashcards based on the criteria provided in the system prompt. Consider the presence of Japanese and English text, and the text clarity.

Based on your assessment, provide your answer in JSON format as specified in the system prompt:

{
  "is_suitable": "Yes" or "No",
  "reason": "A brief explanation for your decision (max 1-2 sentences)"
}

Now, analyze the attached image and provide your JSON response.
"""

flashcard_system_prompt = """
You are an AI assistant specialized in generating structured Anki flashcard data from Japanese language material. You are provided with both raw extracted text and an original image of a Japanese textbook page. Your task is to cross-reference the extracted text with the original image to correct any errors, fill in missing details, and ensure contextually accurate information.

## Strictly follow these rules:
- Use the original image as additional context when processing the extracted text.
- Extract all vocabulary and phrases accurately, correcting any discrepancies using the original image.
- Ensure the **Kanji** column contains the word in Kanji (or Hiragana/Katakana if no Kanji exists).
- Ensure the **Furigana** column contains the phonetic reading of the word in Hiragana.
- Ensure the **English_Translation_and_Notes** column contains both the English translation and any usage or contextual notes present in the source. The usage notes may be in either Japanese or English. Use the surrounding text as context to decide if a given piece of text should be included as a usage note for an existing flashcard or if it should lead to the creation of a new flashcard. In either case, the usage notes must always be placed in the **English_Translation_and_Notes** column.
- Format the output as a valid CSV:
  - Separate fields with commas.
  - Enclose all fields in double quotes (`""`) to handle commas within text.
  - Do **not** include column headers or any other extraneous content that is not part of the data itself.
- **Do not output any additional text, explanations, or formatting instructions—only the CSV content.**

Your role is to transform the raw extracted text into clean, structured CSV data suitable for direct import into Anki, using the original image for enhanced accuracy and context. Pay special attention to elements such as arrows, schematics, and layout cues to ensure accurate and contextually relevant flashcards.
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

flashcard_user_prompt_actual = """
Extract Japanese vocabulary from the provided extracted text and cross-reference it with the supplied original image of a Japanese textbook page. Use additional context from the original image (such as arrows, schematics, or layout cues) to correct any errors in the extracted text. Then, generate Anki flashcards in CSV format with the following columns: **Kanji, Furigana, English_Translation_and_Notes.**

## Instructions:
- Ensure that all Japanese words have their correct **Kanji representation.**
- If a word does not have Kanji, use its Hiragana/Katakana form in the **Kanji** column.
- Include **Furigana readings** in a separate column.
- Provide the **English translation**, along with any **usage notes** from the source. The usage notes may be in either Japanese or English. Use the surrounding text as context to decide if a given piece of text should be used as a usage note for an existing flashcard or be used to create a new flashcard. In either case, the usage notes must always be placed in the **English_Translation_and_Notes** column.
- Cross-reference the extracted text with the original image to fix any inaccuracies and ensure contextual relevance.
- Escape any commas by **enclosing fields in double quotes (`""`)** to maintain CSV integrity.
- The output must **strictly** adhere to CSV format, with no extra explanations or irrelevant text.

## Example Output:
"迷う [道に～]","まよう [みちに～]","lose one's way (e.g., get lost on the road)"
"先輩","せんぱい","senior (student, colleague, etc.)"

Now process the extracted text (between the demarcation markers) and the original image (attached) and generate the CSV output.

---EXTRACTED TEXT STARTS HERE---

{extracted_text}

---EXTRACTED TEXT ENDS HERE---
"""





