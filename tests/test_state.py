import pytest
from prompapa.state import UndoStack

def test_empty_stack_has_no_previous():
    assert not UndoStack().can_undo()

def test_push_and_pop():
    s = UndoStack(); s.push("original text")
    assert s.can_undo() and s.pop() == "original text"

def test_pop_removes_entry():
    s = UndoStack(); s.push("hello"); s.pop()
    assert not s.can_undo()

def test_multiple_pushes_stack_lifo():
    s = UndoStack(); s.push("first"); s.push("second")
    assert s.pop() == "second" and s.pop() == "first"
    assert not s.can_undo()

def test_pop_on_empty_returns_none():
    assert UndoStack().pop() is None

def test_clear_empties_stack():
    s = UndoStack(); s.push("a"); s.push("b"); s.clear()
    assert not s.can_undo()

def test_push_empty_string_is_valid():
    s = UndoStack(); s.push("")
    assert s.can_undo() and s.pop() == ""

def test_max_depth_bounded():
    s = UndoStack(max_depth=3)
    for i in range(10):
        s.push(str(i))
    results = []
    while s.can_undo():
        results.append(s.pop())
    assert results == ["9", "8", "7"]
