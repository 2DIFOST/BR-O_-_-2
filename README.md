# depgraph — визуализатор графа зависимостей Maven

Практическая работа №2 по дисциплине «Конфигурационное управление»,
вариант 19. Инструмент строит граф зависимостей пакета Java (Maven) и
рисует его. Менеджеры пакетов и библиотеки для получения зависимостей не
используются: POM-файлы читаются и разбираются самостоятельно. Приложение
написано на Python 3.10+ и использует только стандартную библиотеку.

Состояние работы: **этап 3 — основные операции** (транзитивный граф, BFS).

## 1. Общее описание

Приложение запускается из командной строки и настраивается только её
опциями. Оно скачивает POM-файлы пакета и его зависимостей из репозитория
Maven (по URL `http`, `https` или `file`), строит граф зависимостей с учётом
транзитивности и печатает его: уровни, зависимости и циклы.

Граф строится обходом в ширину (BFS) без рекурсии. Максимальная глубина и
фильтр по подстроке задаются пользователем, циклические зависимости
обрабатываются корректно. Вместо реального репозитория можно указать файл
тестового репозитория, где пакеты называются большими латинскими буквами.

## 2. Описание функций и настроек

| Опция               | Описание                                      | По умолчанию        |
|---------------------|-----------------------------------------------|---------------------|
| `-p`, `--package`   | анализируемый пакет (см. ниже)                | обязательна         |
| `-r`, `--repo`      | URL репозитория или файл тестового репозитория| Maven Central       |
| `-m`, `--mode`      | `url` — репозиторий Maven, `test` — файл      | `url`               |
| `-o`, `--output`    | имя PNG-файла с изображением графа            | `graph.png`         |
| `-d`, `--max-depth` | максимальная глубина анализа (целое число ≥ 1)| `3`                 |
| `-f`, `--filter`    | пропускать пакеты, в имени которых есть строка| пусто (нет фильтра) |

* `--package`: в режиме `url` — `groupId:artifactId:version`, в режиме
  `test` — имя из больших латинских букв, например `A`;
* `--repo`: URL со схемой `http`, `https` или `file`; по умолчанию
  `https://repo1.maven.org/maven2`; в режиме `test` — путь к файлу
  тестового репозитория (обязателен).

Проверка параметров. При ошибке печатается сообщение `error: ...` в stderr:

* пакет: в режиме `url` нужны три непустые части `groupId:artifactId:version`
  из букв, цифр и символов `._-`; в режиме `test` — только `A`–`Z`;
* репозиторий: допустимы схемы `http`, `https`, `file`, у `http(s)` должен
  быть хост; в режиме `test` обязателен существующий читаемый файл;
* режим: только `url` или `test`;
* изображение: расширение `.png`, существующий и доступный для записи каталог;
* глубина: целое число не меньше 1.

Граф: корень имеет глубину 0, его прямые зависимости — глубину 1 и так далее.
Пакеты глубже `--max-depth` не посещаются. Пакет, имя которого (для Maven
`groupId:artifactId`, без версии) содержит строку `--filter`, и всё, что
доступно только через него, в граф не попадает. Если фильтру соответствует
сам анализируемый пакет, это ошибка параметров.

Коды завершения: `0` — успех, `1` — ошибка репозитория (пакет не найден,
нет сети, неверный POM), `2` — неверные параметры.

### Как читаются зависимости Maven

URL POM-файла: `<репозиторий>/<groupId с / вместо .>/<artifactId>/<версия>/<artifactId>-<версия>.pom`.
Реализованы правила Maven, нужные для прямых зависимостей:

* **родительские POM** (`<parent>`): свойства и `<dependencies>` родителей
  наследуются, зависимость потомка скрывает такую же зависимость родителя;
* **свойства**: `${имя}` берётся из `<properties>` пакета и его родителей, а
  также `${project.version}`, `${project.groupId}`, `${project.parent.version}`
  и аналогичные (`pom.*`, `parent.*`);
* **версия не указана**: берётся из `<dependencyManagement>` пакета и его
  родителей, включая импортируемые BOM (`<scope>import</scope>`, `<type>pom</type>`);
* **диапазон версий** `[1.0,2.0)` заменяется нижней границей `1.0`;
* учитываются только зависимости с областью `compile` (по умолчанию) и
  `runtime`, помеченные `optional` пропускаются; `test`, `provided` и
  `system` в граф не попадают;
* зависимость без определимой версии пропускается с предупреждением
  `warning:` в stderr.

Узел графа — `groupId:artifactId:version`. Разные версии одного пакета
(например, `common-utils:1.1.0` и `common-utils:1.2.0`) — разные узлы.
Если POM зависимости не найден, пакет остаётся в графе без зависимостей, а
в stderr печатается `warning:`. Для самого анализируемого пакета это ошибка.

Не поддерживаются `<exclusions>`, профили, SNAPSHOT-метаданные, `RELEASE` и
`LATEST`, классификаторы.

### Тестовый репозиторий

Режим `--mode test` читает файл, в каждой строке которого описан один пакет:

```text
# комментарий
A: B C
B: D
C: D
D:
```

Имена состоят из заглавных букв `A`–`Z`. Пакет, который встречается только в
списке зависимостей, считается пакетом без зависимостей. Пустые строки и
текст после `#` игнорируются. Ошибки формата сообщаются с номером строки:
нет двоеточия, неверное имя, пакет описан дважды. Примеры лежат в
`examples/test-repos/`.

### Вывод

```text
Dependency graph of <пакет> (max depth N, no filter | filter 'строка')
Packages: <число пакетов>, dependencies: <число зависимостей>
Level 0: <корень>
Level 1: <пакеты глубины 1>
...
Dependencies:
  <пакет> -> <его зависимость>
Cycles: none | <число циклов>
  A -> B -> C -> A
```

## 3. Сборка и тесты

Сборка не нужна. Требуется Python 3.10 или новее (в Windows команда `py`).

```bash
make test                      # модульные тесты
sh scripts/demo_stage1.sh      # параметры и ошибки
sh scripts/demo_stage2.sh      # прямые зависимости
sh scripts/demo_stage3.sh      # граф, глубина, фильтр, циклы, тестовый режим
```

Без `make`: `PYTHONPATH=src python3 -m unittest discover -s tests`
(в Windows Git Bash — `PYTHONPATH=src py -m unittest discover -s tests`).

Для проверок без интернета в `examples/maven-repo` лежит маленький
репозиторий Maven с вымышленными пакетами `org.example`. Он подключается как
`file://` URL.

## 4. Примеры использования

Тестовый репозиторий с «ромбом» зависимостей (`examples/test-repos/diamond.txt`):

```bash
./run.sh -p A -m test -r examples/test-repos/diamond.txt
```

```text
Dependency graph of A (max depth 3, no filter)
Packages: 4, dependencies: 4
Level 0: A
Level 1: B, C
Level 2: D
Dependencies:
  A -> B
  A -> C
  B -> D
  C -> D
Cycles: none
```

Цикл `A -> B -> C -> A` (`cycle.txt`):

```bash
./run.sh -p A -m test -r examples/test-repos/cycle.txt
```

```text
Dependency graph of A (max depth 3, no filter)
Packages: 4, dependencies: 4
Level 0: A
Level 1: B
Level 2: C
Level 3: D
Dependencies:
  A -> B
  B -> C
  C -> A
  C -> D
Cycles: 1
  A -> B -> C -> A
```

Ограничение глубины (`chain.txt`: A→B→C→D→E→F) и фильтр (`filter.txt`):

```bash
./run.sh -p A -m test -r examples/test-repos/chain.txt -d 2
./run.sh -p A -m test -r examples/test-repos/filter.txt -f X
```

Первая команда выведет `A -> B` и `B -> C`, вторая не покажет пакет `X`.

Репозиторий Maven (локальный `file://`; для настоящего репозитория — URL
`https://repo1.maven.org/maven2`, он используется по умолчанию):

```bash
./run.sh -p org.example:shop-app:1.0.0 -r file://$PWD/examples/maven-repo -d 2
```

```text
Dependency graph of org.example:shop-app:1.0.0 (max depth 2, no filter)
Packages: 9, dependencies: 10
Level 0: org.example:shop-app:1.0.0
Level 1: org.example:shop-web:1.0.0, org.example:shop-db:1.0.0, org.example:ghost:9.9.9, org.example:logging-api:1.0.0
...
```

Пакет `ghost` отсутствует в репозитории, поэтому в stderr печатается
`warning: org.example:ghost:9.9.9: not found: ...`, а сам пакет остаётся в графе.

Ошибки:

```bash
./run.sh -p Z -m test -r examples/test-repos/diamond.txt
./run.sh -p A -m test -r examples/test-repos/diamond.txt -f A
```

```text
error: package Z is not described in examples/test-repos/diamond.txt
error: filter 'A' excludes the analyzed package A
```
