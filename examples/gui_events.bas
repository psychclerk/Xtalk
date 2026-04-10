GUI.WINDOW.NEW 1, "GUI Events", 460, 260
GUI.LABEL status, "Select an item", 20, 15

GUI.LISTBOX people, 20, 45, 150, 160
GUI.LISTBOX.ADD people, "Alice"
GUI.LISTBOX.ADD people, "Bob"
GUI.LISTBOX.ONSELECT people, on_people_select

GUI.LISTVIEW tasks, "id|task", 190, 45, 240, 160
GUI.LISTVIEW.ADD tasks, "1|Design"
GUI.LISTVIEW.ADD tasks, "2|Build"
GUI.LISTVIEW.ONCLICK tasks, on_task_click
GUI.LISTVIEW.ONDOUBLECLICK tasks, on_task_doubleclick

GUI.SHOW
END

on_people_select:
GUI.LISTBOX.GET person, people
GUI.LABEL.SET status, "ListBox: " + person
END

on_task_click:
GUI.LISTVIEW.GET row, tasks
GUI.LABEL.SET status, "ListView click: " + row
END

on_task_doubleclick:
GUI.LISTVIEW.GET row, tasks
MSGBOX "Double-clicked row: " + row
END
