from typing import Union, List, Tuple

from imgui_bundle import imgui, imgui_ctx, imgui_node_editor as ed # type: ignore


"""
    ed.begin() / ed.end()
"""
class _BeginEndEditor:
    editor_id: str
    size: imgui.ImVec2Like
    
    id_counter: int
    
    def __init__(self, editor_id: str, size: imgui.ImVec2Like = imgui.ImVec2(0.0, 0.0)):
        self.editor_id = editor_id
        self.size = size
        
        self.id_counter = 0
    
    def __enter__(self):
        ed.begin(self.editor_id, self.size)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        ed.end()

    def _reset_id(self):
        self.id_counter = 0
    
    def _next_id(self):
        self.id_counter += 1
        return self.id_counter

def editor(editor_id: str, size: imgui.ImVec2Like = imgui.ImVec2(0.0, 0.0)) -> _BeginEndEditor:
    return _BeginEndEditor(editor_id, size)


"""
    ed.begin_node() / ed.end_node()
"""
class _BeginEndNode:
    editor_ctx: _BeginEndEditor
    node_id: ed.NodeId
    
    def __init__(self, editor_ctx: _BeginEndEditor):
        self.editor_ctx = editor_ctx
    
    def __enter__(self):
        self.node_id = ed.NodeId(self.editor_ctx._next_id())
        ed.begin_node(self.node_id)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        ed.end_node()

def node(editor_ctx: _BeginEndEditor) -> _BeginEndNode:
    return _BeginEndNode(editor_ctx)


"""
    ed.begin_pin() / ed.end_pin()
"""
class _BeginEndPin:
    editor_ctx: _BeginEndEditor
    kind: ed.PinKind
    pin_id: ed.PinId
    
    def __init__(self, editor_ctx: _BeginEndEditor, kind: ed.PinKind):
        self.editor_ctx = editor_ctx
        self.kind = kind
    
    def __enter__(self):
        self.pin_id = ed.PinId(self.editor_ctx._next_id())
        ed.begin_pin(self.pin_id, self.kind)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        ed.end_pin()

def pin(editor_ctx: _BeginEndEditor, kind: ed.PinKind) -> _BeginEndPin:
    return _BeginEndPin(editor_ctx, kind)


"""
    ed.push_style_var() / ed.pop_style_var()
"""
class _PushPopStyleVar:
    _StyleVarHinting = Tuple[int, Union[float, imgui.ImVec2Like, imgui.ImVec4Like]]
    styles: List[_StyleVarHinting]
    
    def __init__(self, styles: Union[_StyleVarHinting, List[_StyleVarHinting]]):
        if isinstance(styles, tuple):
            styles = [styles]
        self.styles = styles

    def __enter__(self):
        for style in self.styles:
            ed.push_style_var(*style)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        ed.pop_style_var(len(self.styles))

def style_var(*args):
    if len(args) == 1:
        return _PushPopStyleVar(args[0])
    else: # len(args) == 2:
        return _PushPopStyleVar((args[0], args[1]))


"""
(跳过 with 内容的黑魔法)
import sys

class ...:
    def _trace(self, frame, event, arg):
        sys.settrace(None)
        raise Exception()
    
    def __enter__(self):
        def set_abort_hook():
            # https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block/12594789#12594789
            # https://github.com/rfk/withhacks
            sys.settrace(lambda *args, **keys: None)
            f = sys._getframe(0)
            while f.f_locals.get("self") is self:
                f = f.f_back
            f.f_trace = self._trace
        
        ...
"""