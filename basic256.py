#!/usr/bin/env python3
"""Basic-256 interpreter with CLI execution and simple GUI scripting."""

from __future__ import annotations

import argparse
import ast
import operator
import random
import re
import sqlite3
import subprocess
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path as SysPath
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter import simpledialog
from typing import Any, Callable


@dataclass
class Instruction:
    op: str
    raw: str
    line: int


SAFE_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

SAFE_CMP_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


class ExpressionEvaluator:
    def __init__(self, env: dict[str, Any], funcs: dict[str, Callable[..., Any]]) -> None:
        self.env = env
        self.funcs = funcs

    def eval(self, expression: str) -> Any:
        node = ast.parse(expression, mode="eval")
        return self._eval_node(node.body)

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.env.get(node.id, 0)
        if isinstance(node, ast.BinOp):
            op = SAFE_BIN_OPS.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported binary operator")
            return op(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +self._eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not self._eval_node(node.operand)
            raise ValueError("Unsupported unary operator")
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value_node in node.values:
                    value = self._eval_node(value_node)
                    if not value:
                        return value
                return value
            if isinstance(node.op, ast.Or):
                for value_node in node.values:
                    value = self._eval_node(value_node)
                    if value:
                        return value
                return value
            raise ValueError("Unsupported boolean operator")
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op_node, comp_node in zip(node.ops, node.comparators):
                op = SAFE_CMP_OPS.get(type(op_node))
                if op is None:
                    raise ValueError("Unsupported comparison operator")
                right = self._eval_node(comp_node)
                if not op(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = self.funcs.get(node.func.id.upper())
            if fn is None:
                raise ValueError(f"Unknown function '{node.func.id}'")
            args = [self._eval_node(arg) for arg in node.args]
            return fn(*args)
        raise ValueError(f"Unsupported expression syntax: {ast.dump(node)}")


class GuiRuntime:
    def __init__(self, interpreter: "BasicInterpreter") -> None:
        self.interpreter = interpreter
        self.root: tk.Tk | None = None
        self.windows: dict[str, tk.Misc] = {}
        self.active_window = "1"
        self.entries: dict[str, tk.Entry] = {}
        self.labels: dict[str, tk.Label] = {}
        self.listboxes: dict[str, tk.Listbox] = {}
        self.listviews: dict[str, ttk.Treeview] = {}

    @staticmethod
    def _wkey(window_id: str, control_name: str) -> str:
        return f"{window_id}:{control_name}"

    def ensure_window(self, window_id: str | None = None) -> tk.Misc:
        wid = window_id or self.active_window
        if wid in self.windows:
            return self.windows[wid]
        if self.root is None:
            self.root = tk.Tk()
            self.root.title("Basic-256")
            self.windows[wid] = self.root
            return self.root
        top = tk.Toplevel(self.root)
        self.windows[wid] = top
        return top

    def window_new(self, window_id: str, title: str, width: int, height: int) -> None:
        window = self.ensure_window(window_id)
        window.title(title)
        window.geometry(f"{width}x{height}")
        self.active_window = window_id

    def use_window(self, window_id: str) -> None:
        self.ensure_window(window_id)
        self.active_window = window_id

    def gui_new(self, title: str, width: int, height: int) -> None:
        self.window_new("1", title, width, height)

    def add_label(self, name: str, text: str, x: int, y: int) -> None:
        window = self.ensure_window()
        lbl = tk.Label(window, text=text)
        lbl.place(x=x, y=y)
        self.labels[self._wkey(self.active_window, name)] = lbl
        self.interpreter.env[name] = lbl

    def label_set(self, name: str, text: Any) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.labels:
            raise RuntimeError(f"Unknown GUI label '{name}'")
        self.labels[key].config(text=str(text))

    def add_input(self, name: str, x: int, y: int, width: int) -> None:
        window = self.ensure_window()
        entry = tk.Entry(window)
        entry.place(x=x, y=y, width=width)
        self.entries[self._wkey(self.active_window, name)] = entry

    def input_set(self, name: str, value: Any) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.entries:
            raise RuntimeError(f"Unknown GUI input '{name}'")
        self.entries[key].delete(0, tk.END)
        self.entries[key].insert(0, str(value))

    def add_button(self, caption: str, callback_label: str, x: int, y: int, width: int, height: int) -> None:
        window = self.ensure_window()

        def on_click() -> None:
            self.interpreter.jump_to_label(callback_label)
            self.interpreter.run_from_current(gui_callback=True)

        btn = tk.Button(window, text=caption, command=on_click)
        btn.place(x=x, y=y, width=width, height=height)

    def add_listbox(self, name: str, x: int, y: int, width: int, height: int) -> None:
        window = self.ensure_window()
        widget = tk.Listbox(window)
        widget.place(x=x, y=y, width=width, height=height)
        self.listboxes[self._wkey(self.active_window, name)] = widget

    def listbox_add(self, name: str, value: Any) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listboxes:
            raise RuntimeError(f"Unknown GUI listbox '{name}'")
        self.listboxes[key].insert(tk.END, str(value))

    def listbox_set(self, name: str, index: int, value: Any) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listboxes:
            raise RuntimeError(f"Unknown GUI listbox '{name}'")
        widget = self.listboxes[key]
        widget.delete(index)
        widget.insert(index, str(value))

    def listbox_delete(self, name: str, index: int) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listboxes:
            raise RuntimeError(f"Unknown GUI listbox '{name}'")
        self.listboxes[key].delete(index)

    def listbox_clear(self, name: str) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listboxes:
            raise RuntimeError(f"Unknown GUI listbox '{name}'")
        self.listboxes[key].delete(0, tk.END)

    def listbox_get_selected(self, name: str) -> str:
        key = self._wkey(self.active_window, name)
        if key not in self.listboxes:
            raise RuntimeError(f"Unknown GUI listbox '{name}'")
        widget = self.listboxes[key]
        selected = widget.curselection()
        if not selected:
            return ""
        return str(widget.get(selected[0]))

    def add_listview(self, name: str, columns: list[str], x: int, y: int, width: int, height: int) -> None:
        window = self.ensure_window()
        view = ttk.Treeview(window, columns=columns, show="headings")
        for col in columns:
            view.heading(col, text=col)
            view.column(col, width=max(60, int(width / max(1, len(columns)))))
        view.place(x=x, y=y, width=width, height=height)
        self.listviews[self._wkey(self.active_window, name)] = view

    def listview_add(self, name: str, values: list[Any]) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        self.listviews[key].insert("", tk.END, values=[str(v) for v in values])

    def listview_count(self, name: str) -> int:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        return len(self.listviews[key].get_children())

    def listview_get_row(self, name: str, index: int) -> list[str]:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        view = self.listviews[key]
        rows = view.get_children()
        if index < 0 or index >= len(rows):
            return []
        item = view.item(rows[index])
        return [str(v) for v in item.get("values", [])]

    def listview_set_row(self, name: str, index: int, values: list[Any]) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        view = self.listviews[key]
        rows = view.get_children()
        if index < 0 or index >= len(rows):
            raise RuntimeError(f"Listview index out of range: {index}")
        view.item(rows[index], values=[str(v) for v in values])

    def listview_delete_row(self, name: str, index: int) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        view = self.listviews[key]
        rows = view.get_children()
        if index < 0 or index >= len(rows):
            raise RuntimeError(f"Listview index out of range: {index}")
        view.delete(rows[index])

    def listview_clear(self, name: str) -> None:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        view = self.listviews[key]
        for row in view.get_children():
            view.delete(row)

    def listview_get_selected(self, name: str) -> list[str]:
        key = self._wkey(self.active_window, name)
        if key not in self.listviews:
            raise RuntimeError(f"Unknown GUI listview '{name}'")
        view = self.listviews[key]
        selected = view.selection()
        if not selected:
            return []
        item = view.item(selected[0])
        return [str(v) for v in item.get("values", [])]

    def get_input(self, name: str) -> str:
        key = self._wkey(self.active_window, name)
        if key not in self.entries:
            raise RuntimeError(f"Unknown GUI input '{name}'")
        return self.entries[key].get()

    def show(self, window_id: str | None = None) -> None:
        window = self.ensure_window(window_id)
        window.deiconify()
        if self.root is not None:
            self.root.mainloop()


class BasicInterpreter:
    def __init__(self, code: str) -> None:
        self.instructions, self.labels, self.loop_pairs = self._parse(code)
        self.env: dict[str, Any] = {}
        self.pc = 0
        self.gui = GuiRuntime(self)
        self.call_stack: list[int] = []
        self.for_stack: list[dict[str, Any]] = []
        self.db: sqlite3.Connection | None = None
        self.funcs: dict[str, Callable[..., Any]] = {
            "LEN": lambda x: len(str(x)),
            "INT": lambda x: int(float(x)),
            "FLOAT": lambda x: float(x),
            "STR": lambda x: str(x),
            "VAL": lambda x: float(x),
            "ABS": lambda x: abs(x),
            "MIN": lambda *args: min(args),
            "MAX": lambda *args: max(args),
            "RND": self._fn_rnd,
            "UPPER": lambda x: str(x).upper(),
            "LOWER": lambda x: str(x).lower(),
            "LEFT": lambda s, n: str(s)[: int(n)],
            "RIGHT": lambda s, n: str(s)[-int(n) :],
            "MID": lambda s, st, ln=None: str(s)[int(st) : int(st) + int(ln)] if ln is not None else str(s)[int(st) :],
            "INSTR": self._fn_instr,
            "SUBSTR": self._fn_substr,
            "TRIM": lambda s: str(s).strip(),
            "LTRIM": lambda s: str(s).lstrip(),
            "RTRIM": lambda s: str(s).rstrip(),
            "REPLACE": lambda s, old, new: str(s).replace(str(old), str(new)),
            "FILEEXIST": lambda p: SysPath(str(p)).exists(),
            "FILEREAD": lambda p: SysPath(str(p)).read_text(encoding="utf-8"),
        }

    def _parse(self, code: str) -> tuple[list[Instruction], dict[str, int], dict[int, int]]:
        instructions: list[Instruction] = []
        labels: dict[str, int] = {}
        while_stack: list[int] = []
        loop_pairs: dict[int, int] = {}

        for line_no, raw in enumerate(code.splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("'") or line.startswith("#"):
                continue
            if line.endswith(":"):
                labels[line[:-1].strip()] = len(instructions)
                continue
            op, rest = self._split_op(line)
            inst = Instruction(op=op, raw=rest, line=line_no)
            idx = len(instructions)
            instructions.append(inst)
            if op == "WHILE":
                while_stack.append(idx)
            elif op == "WEND":
                if not while_stack:
                    raise RuntimeError(f"WEND without WHILE at line {line_no}")
                start = while_stack.pop()
                loop_pairs[start] = idx
                loop_pairs[idx] = start

        if while_stack:
            raise RuntimeError("Unclosed WHILE block")
        return instructions, labels, loop_pairs

    @staticmethod
    def _split_op(line: str) -> tuple[str, str]:
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            return parts[0].upper(), ""
        return parts[0].upper(), parts[1].strip()

    @staticmethod
    def _split_csv(text: str) -> list[str]:
        if not text:
            return []
        parts: list[str] = []
        buf: list[str] = []
        in_quote = False
        for ch in text:
            if ch == '"':
                in_quote = not in_quote
            if ch == "," and not in_quote:
                parts.append("".join(buf).strip())
                buf = []
                continue
            buf.append(ch)
        if buf:
            parts.append("".join(buf).strip())
        return parts

    def _eval(self, expression: str) -> Any:
        expression = expression.strip()
        return ExpressionEvaluator(self.env, self.funcs).eval(expression)

    def _fn_rnd(self, *args: Any) -> Any:
        if not args:
            return random.random()
        if len(args) == 1:
            return random.randrange(int(args[0]))
        if len(args) == 2:
            return random.randrange(int(args[0]), int(args[1]))
        raise ValueError("RND() accepts 0, 1, or 2 arguments")

    def jump_to_label(self, label: str) -> None:
        if label not in self.labels:
            raise RuntimeError(f"Unknown label '{label}'")
        self.pc = self.labels[label]

    def run(self) -> None:
        self.run_from_current(gui_callback=False)

    def run_from_current(self, gui_callback: bool) -> None:
        while self.pc < len(self.instructions):
            inst = self.instructions[self.pc]
            self.pc += 1
            op, raw = inst.op, inst.raw

            if op == "PRINT":
                print(self._eval(raw))
            elif op == "LET":
                if "=" not in raw:
                    raise RuntimeError(f"LET requires '=' at line {inst.line}")
                name, expr = raw.split("=", 1)
                self.env[name.strip()] = self._eval(expr)
            elif op == "INPUT":
                var = raw.strip()
                self.env[var] = input(f"{var}: ")
            elif op == "IF":
                m = re.match(r"^(.*?)\s+THEN\s+(.*)$", raw, flags=re.IGNORECASE)
                if not m:
                    raise RuntimeError(f"IF missing THEN at line {inst.line}")
                expr, statement = m.groups()
                if self._eval(expr):
                    self._execute_inline(statement)
            elif op == "GOTO":
                self.jump_to_label(raw)
            elif op == "GOSUB":
                self.call_stack.append(self.pc)
                self.jump_to_label(raw)
            elif op == "RETURN":
                if not self.call_stack:
                    raise RuntimeError(f"RETURN without GOSUB at line {inst.line}")
                self.pc = self.call_stack.pop()
            elif op == "WHILE":
                if not self._eval(raw):
                    self.pc = self.loop_pairs[self.pc - 1] + 1
            elif op == "WEND":
                start = self.loop_pairs[self.pc - 1]
                cond = self.instructions[start].raw
                if self._eval(cond):
                    self.pc = start + 1
            elif op == "FOR":
                self._exec_for(raw, inst.line)
            elif op == "NEXT":
                self._exec_next(raw, inst.line)
            elif op == "MSGBOX":
                messagebox.showinfo("Basic-256", str(self._eval(raw)))
            elif op == "GUI.NEW":
                title, width, height = self._split_csv(raw)
                self.gui.gui_new(str(self._eval(title)), int(self._eval(width)), int(self._eval(height)))
            elif op == "GUI.WINDOW.NEW":
                window_id, title, width, height = self._split_csv(raw)
                self.gui.window_new(str(self._eval(window_id)), str(self._eval(title)), int(self._eval(width)), int(self._eval(height)))
            elif op == "GUI.WINDOW.USE":
                self.gui.use_window(str(self._eval(raw)))
            elif op == "GUI.LABEL":
                name, text, x, y = self._split_csv(raw)
                self.gui.add_label(name, str(self._eval(text)), int(self._eval(x)), int(self._eval(y)))
            elif op == "GUI.LABEL.SET":
                name, text = self._split_csv(raw)
                self.gui.label_set(name, self._eval(text))
            elif op == "GUI.INPUT":
                name, x, y, width = self._split_csv(raw)
                self.gui.add_input(name, int(self._eval(x)), int(self._eval(y)), int(self._eval(width)))
            elif op == "GUI.INPUT.SET":
                name, value = self._split_csv(raw)
                self.gui.input_set(name, self._eval(value))
            elif op == "GUI.BUTTON":
                caption, callback, x, y, width, height = self._split_csv(raw)
                self.gui.add_button(str(self._eval(caption)), callback, int(self._eval(x)), int(self._eval(y)), int(self._eval(width)), int(self._eval(height)))
            elif op == "GUI.GET":
                var, input_name = self._split_csv(raw)
                self.env[var] = self.gui.get_input(input_name)
            elif op == "GUI.LISTBOX":
                name, x, y, width, height = self._split_csv(raw)
                self.gui.add_listbox(name, int(self._eval(x)), int(self._eval(y)), int(self._eval(width)), int(self._eval(height)))
            elif op == "GUI.LISTBOX.ADD":
                name, value = self._split_csv(raw)
                self.gui.listbox_add(name, self._eval(value))
            elif op == "GUI.LISTBOX.SET":
                name, index, value = self._split_csv(raw)
                self.gui.listbox_set(name, int(self._eval(index)), self._eval(value))
            elif op == "GUI.LISTBOX.DELETE":
                name, index = self._split_csv(raw)
                self.gui.listbox_delete(name, int(self._eval(index)))
            elif op == "GUI.LISTBOX.CLEAR":
                self.gui.listbox_clear(raw.strip())
            elif op == "GUI.LISTBOX.GET":
                var, name = self._split_csv(raw)
                self.env[var] = self.gui.listbox_get_selected(name)
            elif op == "GUI.LISTVIEW":
                name, columns_text, x, y, width, height = self._split_csv(raw)
                columns = [c.strip() for c in str(self._eval(columns_text)).split("|") if c.strip()]
                if not columns:
                    raise RuntimeError(f"GUI.LISTVIEW requires at least one column at line {inst.line}")
                self.gui.add_listview(name, columns, int(self._eval(x)), int(self._eval(y)), int(self._eval(width)), int(self._eval(height)))
            elif op == "GUI.LISTVIEW.ADD":
                name, values_text = self._split_csv(raw)
                values = [v.strip() for v in str(self._eval(values_text)).split("|")]
                self.gui.listview_add(name, values)
            elif op == "GUI.LISTVIEW.COUNT":
                var, name = self._split_csv(raw)
                self.env[var] = self.gui.listview_count(name)
            elif op == "GUI.LISTVIEW.GETROW":
                var, name, index = self._split_csv(raw)
                self.env[var] = "|".join(self.gui.listview_get_row(name, int(self._eval(index))))
            elif op == "GUI.LISTVIEW.SETROW":
                name, index, values_text = self._split_csv(raw)
                values = [v.strip() for v in str(self._eval(values_text)).split("|")]
                self.gui.listview_set_row(name, int(self._eval(index)), values)
            elif op == "GUI.LISTVIEW.DELETEROW":
                name, index = self._split_csv(raw)
                self.gui.listview_delete_row(name, int(self._eval(index)))
            elif op == "GUI.LISTVIEW.CLEAR":
                self.gui.listview_clear(raw.strip())
            elif op == "GUI.LISTVIEW.GET":
                var, name = self._split_csv(raw)
                self.env[var] = "|".join(self.gui.listview_get_selected(name))
            elif op == "GUI.SHOW":
                show_args = self._split_csv(raw)
                if show_args:
                    self.gui.show(str(self._eval(show_args[0])))
                else:
                    self.gui.show()
                if gui_callback:
                    return
            elif op == "DB.OPEN":
                path = str(self._eval(raw))
                self.db = sqlite3.connect(path)
            elif op == "DB.EXEC":
                self._require_db(inst.line).execute(str(self._eval(raw)))
                self._require_db(inst.line).commit()
            elif op == "DB.QUERY":
                var, sql_expr = self._split_csv(raw)
                rows = self._require_db(inst.line).execute(str(self._eval(sql_expr))).fetchall()
                self.env[var] = rows
            elif op == "DB.SCALAR":
                var, sql_expr = self._split_csv(raw)
                row = self._require_db(inst.line).execute(str(self._eval(sql_expr))).fetchone()
                self.env[var] = row[0] if row else None
            elif op == "DB.CLOSE":
                if self.db is not None:
                    self.db.close()
                    self.db = None
            elif op == "SLEEP":
                time.sleep(float(self._eval(raw)) / 1000.0)
            elif op == "RUN":
                result = subprocess.run(str(self._eval(raw)), shell=True, check=False)
                self.env["A_LASTEXITCODE"] = result.returncode
            elif op == "FILEWRITE":
                path_expr, content_expr = self._split_csv(raw)
                SysPath(str(self._eval(path_expr))).write_text(str(self._eval(content_expr)), encoding="utf-8")
            elif op == "INPUTBOX":
                var, prompt, *title = self._split_csv(raw)
                root = self.gui.ensure_window("1")
                root.withdraw()
                text = simpledialog.askstring(
                    str(self._eval(title[0])) if title else "Input",
                    str(self._eval(prompt)),
                    parent=root,
                )
                root.deiconify()
                self.env[var] = text if text is not None else ""
            elif op == "END":
                if self.db is not None:
                    self.db.close()
                    self.db = None
                return
            else:
                raise RuntimeError(f"Unknown op {op} at line {inst.line}")

            if gui_callback:
                return

    def _exec_for(self, raw: str, line: int) -> None:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s+TO\s+(.*?)(?:\s+STEP\s+(.*))?$", raw, flags=re.IGNORECASE)
        if not m:
            raise RuntimeError(f"Invalid FOR syntax at line {line}")
        var, start, end, step = m.groups()
        step_val = self._eval(step) if step is not None else 1
        self.env[var] = self._eval(start)
        self.for_stack.append({"var": var, "end": self._eval(end), "step": step_val, "start_pc": self.pc})

    def _exec_next(self, raw: str, line: int) -> None:
        if not self.for_stack:
            raise RuntimeError(f"NEXT without FOR at line {line}")
        frame = self.for_stack[-1]
        var = raw.strip() or frame["var"]
        if var != frame["var"]:
            raise RuntimeError(f"NEXT variable mismatch at line {line}")
        self.env[var] = self.env.get(var, 0) + frame["step"]
        value = self.env[var]
        end = frame["end"]
        step = frame["step"]
        should_continue = value <= end if step >= 0 else value >= end
        if should_continue:
            self.pc = frame["start_pc"]
        else:
            self.for_stack.pop()

    def _execute_inline(self, statement: str) -> None:
        op, raw = self._split_op(statement)
        self.instructions.insert(self.pc, Instruction(op=op, raw=raw, line=-1))

    def _require_db(self, line: int) -> sqlite3.Connection:
        if self.db is None:
            raise RuntimeError(f"Database is not open at line {line}")
        return self.db

    def _fn_instr(self, haystack: Any, needle: Any, start: Any = 0) -> int:
        return str(haystack).find(str(needle), int(start))

    def _fn_substr(self, text: Any, start: Any, length: Any | None = None) -> str:
        s = str(text)
        idx = int(start)
        if idx < 0:
            idx = len(s) + idx
        if length is None:
            return s[idx:]
        return s[idx : idx + int(length)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Basic-256 interpreter")
    parser.add_argument("script", type=Path, help="Path to .bas file")
    args = parser.parse_args(argv)

    if not args.script.exists():
        print(f"Script not found: {args.script}", file=sys.stderr)
        return 1

    code = args.script.read_text(encoding="utf-8")
    BasicInterpreter(code).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
