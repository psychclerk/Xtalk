GUI.NEW "Counter App", 300, 140
GUI.LABEL title, "Mini app (AHK v1-style flow)", 20, 10
GUI.INPUT amount, 20, 40, 120
GUI.BUTTON "Show", on_show, 170, 40, 90, 28
GUI.LISTBOX items, 20, 80, 120, 50
GUI.LISTBOX.ADD items, "One"
GUI.LISTBOX.ADD items, "Two"
GUI.SHOW
END

on_show:
GUI.GET value, amount
GUI.LISTBOX.GET selected, items
MSGBOX "You entered: " + value + " / selected: " + selected
END
