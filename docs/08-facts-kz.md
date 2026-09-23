# Факты и источники

Всё, что произносим со сцены и пишем в README, должно опираться на строку отсюда.
Проверено 17–23.09.2026.

## Программа и планирование

- Типовые учебные программы по общеобразовательным предметам — приказ, приложения по предметам:
  https://adilet.zan.kz/rus/docs/V1300008424 (и https://adilet.zan.kz/rus/docs/V13008424_4)
- Типовые учебные планы (часы по классам и предметам): https://adilet.zan.kz/rus/docs/V1200008170
- Внутри программ — долгосрочный план: цели обучения по четвертям и разделам, код вида `7.2.1.4`.
- Иерархия планирования учителя: ДСП → ССП → КСП. КСП обязателен на каждый урок.
- Рынок готовых планов: https://plani.kz/

## Оценивание

- В 1 классе учебные достижения **не оцениваются**; баллы, СОР и СОЧ — со 2 класса.
  https://www.zakon.kz/obshestvo/6390904-v-kazakhstane-izmenilis-pravila-kontrolya-uspevaemosti-shkolnikov.html
- Как считаются четвертные баллы (СОР/СОЧ):
  https://edu.mcfr.kz/article/4337-kak-rasschityvayutsya-otsenki-po-ballam-v-shkolah-kazahstana
- Министерство: сборники СОР/СОЧ разошлись по интернету, учитель их для оценивания не использует.
  https://informburo.kz/novosti/mon-o-razmeshchenii-sbornikov-sor-i-soch-v-internete-uchitel-ne-ispolzuet-ih-pri-ocenivanii.html
- Спецификация, критерии, дескрипторы: https://class-kz.ru/summativnoe-ocenivanie/
- Правила меняются (обсуждается замена СОЧ промежуточным оцениванием после раздела) →
  схема выставления баллов должна быть конфигом, а не кодом.

## Устройства и доступ

- Две из пяти семей не имеют компьютера или ноутбука:
  https://energyprom.kz/articles-ru/industries-ru/dve-iz-pyati-kazahstanskih-semej-ne-imeyut-kompyutera-ili-noutbuka/
- Мобильный интернет — 96,7% домохозяйств, в Акмолинской области 81,2%:
  https://bes.media/news/pochti-kazhdaya-pyataya-semya-v-odnoy-oblasti-kazahstana-zhivet-bez-interneta/
- Треть сельских школ оснащена базовыми техсредствами:
  https://inform.kz/ru/kakkazahstan-vgod-iizhivet-podvum-raznim-standartam-ikto-neset-zaeto-otvetstvenn-526520ec

## Телефоны в школе

- С мая 2026 использование телефонов на уроках запрещено, **кроме предусмотренного
  календарно-тематическим планом**:
  https://www.zakon.kz/stati/6529487-telefony-na-urokakh-zapreshcheny-chto-nado-znat-shkolnikam-i-roditelyam-v-kazakhstane.html
  https://tengrinews.kz/newseducation/smartfonyi-shkolah-otvetstvennost-uchiteley-kazahstane-600236/

## Почему не парсим учебники

- Агрегаторы PDF без явной лицензии: https://okulyk.kz/ , https://topiq.kz/ru/
  Права у издательств (Атамұра, Мектеп, Алматыкітап).
- Открытые зарубежные источники не спасают: Common Core — не открытая лицензия
  (https://www.thecorestandards.org/public-license/), CK-12 и Khan Academy — CC BY-NC(-SA),
  то есть запрет коммерческого использования; у OpenStax часть книг NC-SA.

## Детекторы ИИ

- Ложные срабатывания у неносителей языка — 61,3% против 1–4% у носителей;
  Vanderbilt отключил детектор Turnitin.
  https://www.researchgate.net/publication/403249541_AI_writing_detectors_are_ineffective_unreliable_and_harmful
  https://lawlibguides.sandiego.edu/c.php?g=1443311&p=10721367
- Рукописное распознавание на кириллице: 60–85% точности.
  https://habr.com/ru/companies/mts_ai/articles/1065182/

## Күнделік

- API есть, но доступ только по OAuth2 с ручной выдачей client_id через форму для разработчиков:
  https://api.kundelik.kz/ , https://company.kundelik.kz/developers/

## Конкуренты

- Bilim AI — бесплатный ИИ-репетитор, каз/рус: https://bilim-ai.kz/
- WONK — ИИ-репетитор в школах:
  https://ru.elordainfo.kz/obrazovaniye/wonk-vnedryaet-ii-v-shkoly-kak-kazahstanskiy-startap-menyaet-obrazovanie
- iTest / BilimLand — тренажёр ЕНТ, 16 тыс. вопросов: https://bilimland.kz/

## Модели

- Казахские открытые: ISSAI KazLLM 8B/70B (https://issai.nu.edu.kz/ru/kazllm-rus/),
  Sherkala 8B от Inception/MBZUAI — обходит KazLLM 8B на MMLU.
- Бесплатные тиры для фолбэка: Google AI Studio (Gemini), Groq (~30 rpm / 1000 в сутки),
  OpenRouter free (20 rpm / 50 запросов в день).
- Эмбеддинги для поиска по целям: BGE-m3, multilingual-e5.
