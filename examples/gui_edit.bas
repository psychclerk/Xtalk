GUI.WINDOW.NEW 1, "Edit Demo", 420, 260
GUI.LABEL status, "Ready", 20, 15
GUI.INPUT nameInput, 20, 45, 160
GUI.INPUT.SET nameInput, "Alice"

GUI.LISTBOX users, 20, 80, 160, 120
GUI.LISTBOX.ADD users, "Alice"
GUI.LISTBOX.ADD users, "Bob"
GUI.LISTBOX.SET users, 1, "Robert"

GUI.LISTVIEW tasks, "id|task", 200, 45, 190, 155
GUI.LISTVIEW.ADD tasks, "1|Build"
GUI.LISTVIEW.ADD tasks, "2|Test"
GUI.LISTVIEW.SETROW tasks, 1, "2|Deploy"
GUI.LISTVIEW.COUNT taskCount, tasks
GUI.LABEL.SET status, "Rows: " + STR(taskCount)

GUI.BUTTON "Show selected", on_show, 200, 205, 120, 30
GUI.SHOW
END

on_show:
GUI.GET who, nameInput
GUI.LISTBOX.GET selUser, users
GUI.LISTVIEW.GET row, tasks
MSGBOX "Input=" + who + ", User=" + selUser + ", Row=" + row
END
