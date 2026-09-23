PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS business (
  id       INTEGER PRIMARY KEY,
  name     TEXT NOT NULL,
  industry TEXT,
  contact  TEXT
);

-- профиль студенческой команды: без персональных и чувствительных признаков (ТЗ §5)
CREATE TABLE IF NOT EXISTS team (
  id           INTEGER PRIMARY KEY,
  name         TEXT NOT NULL,
  interests    TEXT DEFAULT '[]',
  skills       TEXT DEFAULT '[]',
  technologies TEXT DEFAULT '[]',
  points       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS task (
  id             INTEGER PRIMARY KEY,
  business_id    INTEGER NOT NULL REFERENCES business(id),
  industry       TEXT,
  draft_text     TEXT NOT NULL,
  status         TEXT DEFAULT 'new',     -- new | card | published
  card           TEXT DEFAULT '{}',      -- текущая редактируемая карточка
  sources        TEXT DEFAULT '{}',      -- поле → дословная цитата из текста пользователя или "manual"
  confirmed      INTEGER DEFAULT 0,      -- текущая карточка подтверждена бизнесом
  confirmed_card TEXT,                   -- последняя подтверждённая версия: по ней официальный рейтинг
  score          INTEGER,                -- официальный рейтинг, считается по confirmed_card
  level          TEXT,                   -- draft | working | ready | priority
  ai_meta        TEXT DEFAULT '{}',      -- mode (llm | stub), attempts, warnings
  privacy        TEXT DEFAULT '[]',      -- что замаскировано: ИИН, номера карт (privacy.py)
  created_at     TEXT DEFAULT (datetime('now')),
  published_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_task_catalog ON task(status, score);

CREATE TABLE IF NOT EXISTS question (
  id         INTEGER PRIMARY KEY,
  task_id    INTEGER NOT NULL REFERENCES task(id),
  field      TEXT NOT NULL,              -- поле карточки, которое уточняет вопрос
  text       TEXT NOT NULL,
  answer     TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- лента роста рейтинга: главный кадр демо
CREATE TABLE IF NOT EXISTS rating_event (
  id         INTEGER PRIMARY KEY,
  task_id    INTEGER NOT NULL REFERENCES task(id),
  event      TEXT NOT NULL,              -- draft | answers | edit | confirm
  score      INTEGER NOT NULL,
  level      TEXT NOT NULL,
  confirmed  INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS proposal (
  id         INTEGER PRIMARY KEY,
  task_id    INTEGER NOT NULL REFERENCES task(id),
  team_id    INTEGER NOT NULL REFERENCES team(id),
  idea       TEXT NOT NULL,
  plan       TEXT NOT NULL,
  timeline   TEXT NOT NULL,
  link       TEXT NOT NULL,
  status     TEXT DEFAULT 'submitted',   -- submitted | accepted | rejected; решает только бизнес
  comment    TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  decided_at TEXT
);

-- MVP-2: подтверждённый бизнесом этап → баллы команде за фактический прогресс
CREATE TABLE IF NOT EXISTS milestone (
  id          INTEGER PRIMARY KEY,
  proposal_id INTEGER NOT NULL REFERENCES proposal(id),
  title       TEXT NOT NULL,
  points      INTEGER DEFAULT 10,
  created_at  TEXT DEFAULT (datetime('now'))
);
