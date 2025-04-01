import sys
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
    ed.link()
"""
def link(editor_ctx: _BeginEndEditor, input_pin_id: ed.PinId, output_pin_id: ed.PinId) -> None:
    l_id = ed.LinkId(editor_ctx._next_id())
    ed.link(l_id, input_pin_id, output_pin_id)


"""
    skip with block
"""
class _Abortable:
    class AbortException(Exception): pass
    
    def _trace(self, frame, event, arg):
        sys.settrace(None)
        raise _Abortable.AbortException()
    
    def set_abort_hook(self):
        # https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block/12594789#12594789
        # https://github.com/rfk/withhacks
        sys.settrace(lambda *args, **keys: None)
        f = sys._getframe(0)
        while f.f_locals.get("self") is self:
            f = f.f_back
        f.f_trace = self._trace


"""
    ed.begin_create() / ed.end_create()
"""
class _BeginEndCreate(_Abortable):
    def __enter__(self):
        if not ed.begin_create():
            self.set_abort_hook()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is _Abortable.AbortException:
            return True
        
        ed.end_create()

def on_create() -> _BeginEndCreate:
    return _BeginEndCreate()


"""
    ed.query_new_link()
"""
class _QueryNewLink(_Abortable):
    def __enter__(self):
        input_pin_id, output_pin_id = ed.PinId(), ed.PinId()
        if not ed.query_new_link(input_pin_id, output_pin_id):
            self.set_abort_hook()
        if not input_pin_id or not output_pin_id:
            self.set_abort_hook()
        return input_pin_id, output_pin_id
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is _Abortable.AbortException:
            return True

def new_link() -> Tuple[ed.PinId, ed.PinId]:
    return _QueryNewLink()


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

