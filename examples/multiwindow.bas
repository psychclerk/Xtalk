GUI.WINDOW.NEW 1, "Main Window", 320, 180
GUI.LABEL lbl1, "This is window 1", 20, 20
GUI.BUTTON "Open message", show_main, 20, 60, 140, 30

GUI.WINDOW.NEW 2, "Tool Window", 280, 180
GUI.WINDOW.USE 2
GUI.LABEL lbl2, "This is window 2", 20, 20
GUI.INPUT userText, 20, 60, 180
GUI.BUTTON "Read text", show_tool, 20, 100, 120, 30

GUI.WINDOW.USE 1
GUI.SHOW
END

show_main:
MSGBOX "Main window callback"
END

show_tool:
GUI.WINDOW.USE 2
GUI.GET typed, userText
MSGBOX "Window 2 says: " + typed
END
