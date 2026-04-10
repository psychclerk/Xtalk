LET text = "  hello world  "
PRINT TRIM(text)
PRINT INSTR(text, "world")
PRINT SUBSTR("abcdef", 2, 3)
LET replaced = REPLACE("a-b-c", "-", ":")
PRINT replaced

FILEWRITE "examples/tmp_note.txt", "demo"
PRINT FILEEXIST("examples/tmp_note.txt")
PRINT FILEREAD("examples/tmp_note.txt")

RUN "echo from run command"
PRINT A_LASTEXITCODE
END
