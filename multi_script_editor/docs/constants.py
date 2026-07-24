HELP_TEXT = """<html>
	<head>
		<title></title>
	</head>
	<body>
		<h2>
			Multi Script Editor v%s</h2>
		<br>
		<p>
			By PaulWinex paulwinex.com</p>
		<p>
			By Carlos Rico Adega</p>
		<br>
		<h3>
			Editor Variables:</h3>
		<ul>
			<br>
			<li>
				<strong>self_main</strong>: (QWidget) main widget</li>
			<li>
				<strong>self_output</strong>: (QWidget) output widget</li>
			<li>
				<strong>self_version</strong>: (string) current version</li>
			<li>
				<strong>self_context</strong>: (string or None) current context</li>
			<li>
				<strong>self_help</strong>: (function) show this text</li>
		</ul>
		<p><br/></p>
	</body>
</html>"""

SHORTCUTS_TEXT = """Execute All                                 >   ALT + ENTER
Clear Output & Execute All                  >   ALT + SHIFT + ENTER
Execute Selected                            >   CTRL + ENTER
Clear Output & Execute Selected             >   CTRL + SHIFT + ENTER
Execute Line                                >   CTRL + ALT + ENTER
Clear Output & Execute Line                 >   CTRL + ALT + SHIFT + ENTER
Indent Selection                            >   TAB
Unindent Selection                          >   SHIFT + TAB
Activate Completer                          >   UP or DOWN
Deactivate Completer                        >   BACKSPACE or one char
Hide Completer                              >   ESC
Autocomplete code                           >   ENTER (in Completer)
Autocomplete first                          >   ENTER or TAB in Editor
Force Autocomplete                          >   CTRL + SPACE
Font Size                                   >   CTRL + MouseWheel
Scroll Code Left-Right                      >   ALT + MouseWheel
Comment/Uncomment line or selected lines    >   ALT + C
Move line(s) up                             >   ALT + UP
Move line(s) down                           >   ALT + DOWN
Run dir() on current word                   >   ALT + D
Run help() on current word                  >   ALT + H
Quick Help                                  >   F1
Add Quotes                                  >   ALT + Q
Print Command                               >   ALT + E
Autocomplete                                >   ALT + A
Run type() on current word                  >   ALT + T
Toggle Word Wrap                            >   ALT + W
Toggle Clear Output before Execute          >   CTRL + ALT + C
Toggle Output Word Wrap                     >   CTRL + ALT + W
Toggle Always On Top                        >   CTRL + ALT + T
Compare with...                             >   CTRL + SHIFT + C
Clear Output                                >   CTRL + ALT + SHIFT + C
Duplicate line(s) or selected text          >   CTRL + SHIFT + D
Select Next Occurrence                      >   CTRL + ALT + D
Select All Occurrences                      >   CTRL + SHIFT + ALT + D
Copy                                        >   CTRL + C
Delete line(s)                              >   CTRL + D
Add Cursors to line ends                    >   ALT + SHIFT + I
Find and Replace                            >   CTRL + F
Go to Line                                  >   CTRL + G
Paste                                       >   CTRL + V
New Tab                                     >   CTRL + T
Close Tab                                   >   CTRL + W
Cut                                         >   CTRL + X
Redo                                        >   CTRL + Y
Undo                                        >   CTRL + Z
Wrap dropped nodes (Maya and Houdini)       >   MMB Drag + ALT
Open File                                   >   CTRL + O
Save File                                   >   CTRL + S
Save Script As                              >   CTRL + SHIFT + S
Save Session                                >   CTRL + ALT + S
Quit                                        >   CTRL + Q
Code Outline                                >   CTRL + SHIFT + O
Toggle Show Whitespace                      >   CTRL + SHIFT + W
Output                                      >   CTRL + J
Output at the bottom                        >   CTRL + U
Toggle Bookmark                             >   CTRL + F2
Next Bookmark                               >   F2
Previous Bookmark                           >   SHIFT + F2
Clear Bookmarks                             >   CTRL + SHIFT + F2
Bookmarks Finder                            >   CTRL + B
Open in browser                             >   CTRL + ALT + B
Clipboard Manager                           >   CTRL + SHIFT + V"""

TESTED_TEXT = """Supported applications:
    Standalone - Python 3

    Autodesk Maya
    SideFx Houdini
    The Foundry Nuke

Tested on:

    Houdini 20.0.1122 · Linux · Python-3.10.10 · PySide2-5.15.2
    Houdini 20.0.751 · Windows · Python-3.10.10 · PySide2-5.15.2
    Houdini 21.0.729 · Windows · Python-3.11.7 · PySide6-6.5.3
    Houdini 22.0.368 · Windows · Python-3.13.10 · PySide-6.8.3

    Maya 2024.2   · Linux   · Python-3.10.8 · PySide-5.15.2.1
    Maya 2024.2.4 · Windows · Python-3.10.8 · PySide-5.15.2.1
    Maya 2025.3.2 · Windows · Python-3.11.4 · PySide6-6.5.3
    Maya 2026.3.4 · Windows · Python-3.11.9 · PySide6-6.5.3
    Maya 2027      · Windows · Python-3.13.9 · PySide6-6.8.3

    Nuke 15.2v9 · Windows · Python-3.10.10 · PySide2-5.15.2.1
    Nuke 17.1v2 · Windows · Python-3.11.11 · PySide6-6.5.3

    Standalone
        Linux   · Python-3.11.12 · PySide6-6.9.2
        Linux   · Python-3.10.13 · PySide2-5.15.2.1
        Windows · Python-3.13.14 · PySide6-6.11.1
        Windows · Python-3.10.11 · PySide2-5.15.2.1"""
