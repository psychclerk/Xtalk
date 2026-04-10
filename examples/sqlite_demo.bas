DB.OPEN ":memory:"
DB.EXEC "CREATE TABLE notes(id INTEGER PRIMARY KEY, title TEXT)"
DB.EXEC "INSERT INTO notes(title) VALUES ('First')"
DB.EXEC "INSERT INTO notes(title) VALUES ('Second')"
DB.SCALAR total, "SELECT COUNT(*) FROM notes"
PRINT "Rows: " + STR(total)
DB.QUERY rows, "SELECT id, title FROM notes ORDER BY id"
PRINT rows
DB.CLOSE
END
