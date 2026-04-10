# Basic-256

Basic-256 is a tiny BASIC-like interpreter with command-line script execution and GUI primitives inspired by AutoHotkey v1-style app scripts.

## Run `.bas` files

```bash
python3 basic256.py examples/hello.bas
```

## Core statements

- `PRINT <expr>`
- `LET name = <expr>`
- `INPUT name`
- `INPUTBOX varName, "Prompt"[, "Title"]`
- `IF <expr> THEN <statement>`
- `GOTO label`
- `GOSUB label`
- `RETURN`
- `WHILE <expr>` / `WEND`
- `FOR i = start TO end [STEP step]` / `NEXT [i]`
- `SLEEP milliseconds`
- `RUN "shell command"` (writes exit code to `A_LASTEXITCODE`)
- `FILEWRITE "path", contentExpr`
- `label:`
- `END`

## Built-in functions

- Numeric: `INT(x)`, `FLOAT(x)`, `VAL(x)`, `ABS(x)`, `MIN(...)`, `MAX(...)`, `RND()`, `RND(max)`, `RND(min, max)`
- String: `STR(x)`, `LEN(x)`, `UPPER(x)`, `LOWER(x)`, `LEFT(s,n)`, `RIGHT(s,n)`, `MID(s,start[,len])`, `SUBSTR(s,start[,len])`, `INSTR(haystack,needle[,start])`, `TRIM(s)`, `LTRIM(s)`, `RTRIM(s)`, `REPLACE(s,old,new)`
- File: `FILEEXIST(path)`, `FILEREAD(path)`

## GUI statements

- Multi-window (AHK v1-style workflow):
  - `GUI.WINDOW.NEW windowId, "Title", width, height`
  - `GUI.WINDOW.USE windowId`
  - then add controls with normal `GUI.*` commands to the active window
- Single-window shorthand:
- `MSGBOX <expr>`
- `GUI.NEW "Title", width, height`
- `GUI.LABEL name, "Text", x, y`
- `GUI.LABEL.SET name, textExpr`
- `GUI.INPUT name, x, y, width`
- `GUI.INPUT.SET name, valueExpr`
- `GUI.BUTTON "Caption", callbackLabel, x, y, width, height`
- `GUI.GET varName, inputName`
- `GUI.LISTBOX name, x, y, width, height`
- `GUI.LISTBOX.ADD name, valueExpr`
- `GUI.LISTBOX.SET name, index, valueExpr`
- `GUI.LISTBOX.DELETE name, index`
- `GUI.LISTBOX.CLEAR name`
- `GUI.LISTBOX.GET varName, listboxName`
- `GUI.LISTVIEW name, "col1|col2|...", x, y, width, height`
- `GUI.LISTVIEW.ADD name, "value1|value2|..."`
- `GUI.LISTVIEW.COUNT varName, listviewName`
- `GUI.LISTVIEW.GETROW varName, listviewName, index`
- `GUI.LISTVIEW.SETROW listviewName, index, "value1|value2|..."`
- `GUI.LISTVIEW.DELETEROW listviewName, index`
- `GUI.LISTVIEW.CLEAR listviewName`
- `GUI.LISTVIEW.GET varName, listviewName`
- `GUI.SHOW [windowId]`

## Database statements (SQLite)

- `DB.OPEN "file.db"` (use `":memory:"` for in-memory DB)
- `DB.EXEC "SQL statement"`
- `DB.QUERY varName, "SELECT ..."` (stores list of rows/tuples)
- `DB.SCALAR varName, "SELECT ..."` (stores first column from first row)
- `DB.CLOSE`

## Notes

- Strings use double quotes.
- Expressions support arithmetic, comparisons, boolean operators, unary `NOT`, and function calls.
