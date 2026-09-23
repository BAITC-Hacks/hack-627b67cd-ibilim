PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS objective (
  code           TEXT PRIMARY KEY,
  grade          INTEGER NOT NULL,
  subject        TEXT    NOT NULL,
  section        TEXT,
  subsection     TEXT,
  quarter        INTEGER,
  hours          INTEGER DEFAULT 0,
  order_index    INTEGER DEFAULT 0,
  text_ru        TEXT NOT NULL,
  text_kk        TEXT,
  prerequisites  TEXT DEFAULT '[]',   -- JSON: ["7.2.1.3"]
  source         TEXT DEFAULT 'DRAFT'
);

CREATE TABLE IF NOT EXISTS textbook (
  id        INTEGER PRIMARY KEY,
  title     TEXT,
  publisher TEXT,
  year      INTEGER,
  grade     INTEGER,
  subject   TEXT
);

-- только метаданные: контента учебника здесь нет и не будет
CREATE TABLE IF NOT EXISTS textbook_unit (
  id              INTEGER PRIMARY KEY,
  textbook_id     INTEGER REFERENCES textbook(id),
  label           TEXT NOT NULL,        -- «§14, стр. 87»
  objective_codes TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS klass (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,            -- «7А»
  grade       INTEGER NOT NULL,
  subject     TEXT NOT NULL,
  language    TEXT DEFAULT 'ru',        -- ru | kk
  textbook_id INTEGER REFERENCES textbook(id)
);

CREATE TABLE IF NOT EXISTS student (
  id       INTEGER PRIMARY KEY,
  klass_id INTEGER NOT NULL REFERENCES klass(id),
  name     TEXT NOT NULL                -- ни почты, ни телефона: принципиально
);

CREATE TABLE IF NOT EXISTS schedule_slot (
  id        INTEGER PRIMARY KEY,
  klass_id  INTEGER NOT NULL REFERENCES klass(id),
  weekday   INTEGER NOT NULL,           -- 1 = понедельник
  lesson_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar (
  id        INTEGER PRIMARY KEY,
  quarter   INTEGER NOT NULL,
  starts_on TEXT NOT NULL,
  ends_on   TEXT NOT NULL,
  holidays  TEXT DEFAULT '[]'           -- JSON: ["2026-10-05"]
);

-- lesson — это и есть КТП
CREATE TABLE IF NOT EXISTS lesson (
  id              INTEGER PRIMARY KEY,
  klass_id        INTEGER NOT NULL REFERENCES klass(id),
  date            TEXT NOT NULL,
  topic           TEXT,
  objective_codes TEXT DEFAULT '[]',
  status          TEXT DEFAULT 'planned'  -- planned | done | skipped
);
CREATE INDEX IF NOT EXISTS idx_lesson_klass_date ON lesson(klass_id, date);

CREATE TABLE IF NOT EXISTS lesson_pack (
  lesson_id         INTEGER PRIMARY KEY REFERENCES lesson(id),
  ksp               TEXT,
  explanation       TEXT,
  common_mistakes   TEXT,
  classwork         TEXT,
  homework_template TEXT,
  model             TEXT,
  created_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gen_cache (
  key        TEXT PRIMARY KEY,          -- sha256(objective+level+lang+PROMPT_VERSION)
  payload    TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS assignment_item (
  id             INTEGER PRIMARY KEY,
  student_id     INTEGER NOT NULL REFERENCES student(id),
  lesson_id      INTEGER NOT NULL REFERENCES lesson(id),
  objective_code TEXT NOT NULL REFERENCES objective(code),
  level          INTEGER DEFAULT 1,
  seed           TEXT DEFAULT '{}',
  statement      TEXT NOT NULL,
  answer         TEXT NOT NULL,         -- эталон, считается кодом (sympy), не моделью
  descriptors    TEXT DEFAULT '[]',
  max_score      INTEGER DEFAULT 2,
  origin         TEXT DEFAULT 'today'   -- today | gap
);
CREATE INDEX IF NOT EXISTS idx_item_student_lesson ON assignment_item(student_id, lesson_id);

CREATE TABLE IF NOT EXISTS submission (
  id         INTEGER PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student(id),
  lesson_id  INTEGER NOT NULL REFERENCES lesson(id),
  channel    TEXT NOT NULL,             -- web | phone | paper
  raw        TEXT,                      -- путь к фото или исходный JSON
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS item_result (
  id                INTEGER PRIMARY KEY,
  submission_id     INTEGER NOT NULL REFERENCES submission(id),
  item_id           INTEGER NOT NULL REFERENCES assignment_item(id),
  answer_raw        TEXT,
  score             INTEGER DEFAULT 0,
  max_score         INTEGER DEFAULT 2,
  correct           INTEGER DEFAULT 0,
  confidence        REAL DEFAULT 0,
  needs_teacher     INTEGER DEFAULT 0,
  descriptors_hit   TEXT DEFAULT '[]',
  feedback          TEXT,
  ai_index          REAL DEFAULT 0,
  ai_reasons        TEXT DEFAULT '[]',
  telemetry         TEXT DEFAULT '{}',
  teacher_confirmed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mastery (
  student_id     INTEGER NOT NULL REFERENCES student(id),
  objective_code TEXT NOT NULL REFERENCES objective(code),
  value          REAL DEFAULT 0,
  attempts       INTEGER DEFAULT 0,
  updated_at     TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (student_id, objective_code)
);
