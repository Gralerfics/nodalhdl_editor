from nodalhdl.core.structure import Structure

import sys
from typing import Dict

from imgui_bundle import imgui, immapp, imgui_node_editor as ed # type: ignore


class NEContext:
    class NEContextException(Exception): pass
    class NEContextSkipException(Exception): pass
    
    Editor = 0
    Node = 1
    Pin = 2
    Creating = 3
    Deleting = 4
    
    def __init__(self, context_type: int, *arg, **kwargs):
        self.context_type = context_type
        self.arg = arg
        self.kwargs = kwargs
    
    def __enter__(self):
        def set_abort_hook():
            # https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block/12594789#12594789
            # https://github.com/rfk/withhacks
            sys.settrace(lambda *args, **keys: None)
            f = sys._getframe(0)
            while f.f_locals.get("self") is self:
                f = f.f_back
            f.f_trace = self.trace
        
        if self.context_type == NEContext.Editor:
            ed.begin(*self.arg, **self.kwargs)
        elif self.context_type == NEContext.Node:
            ed.begin_node(*self.arg, **self.kwargs)
        elif self.context_type == NEContext.Pin:
            ed.begin_pin(*self.arg, **self.kwargs)
        elif self.context_type == NEContext.Creating:
            if not ed.begin_create():
                set_abort_hook()
        elif self.context_type == NEContext.Deleting:
            if not ed.begin_delete():
                set_abort_hook()
        else:
            raise NEContext.NEContextException("Invalid context type")
    
    def trace(self, frame, event, arg):
        sys.settrace(None)
        raise NEContext.NEContextSkipException()
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is NEContext.NEContextSkipException:
            return True
        
        if self.context_type == NEContext.Editor:
            ed.end()
        elif self.context_type == NEContext.Node:
            ed.end_node()
        elif self.context_type == NEContext.Pin:
            ed.end_pin()
        elif self.context_type == NEContext.Creating:
            ed.end_create()
        elif self.context_type == NEContext.Deleting:
            ed.end_delete()
        else:
            raise NEContext.NEContextException("Invalid context type")


class StructureState:
    def __init__(self, structure: Structure = None):
        self.structure = Structure() if structure is None else structure

class StructureEditor:
    def __init__(self):
        self.state: StructureState = StructureState()
        
        ed_config = ed.Config()
        ed_config.settings_file = ""
        self.context = ed.create_editor(ed_config)
        
        self.gui_is_first_frame = True
        
        self.next_link_id = 1000 # TODO
    
    def __del__(self):
        ed.destroy_editor(self.context)
    
    def select(self):
        ed.set_current_editor(self.context)
    
    def gui(self):
        self.select()
        
        with NEContext(NEContext.Editor, "Editor", imgui.ImVec2(0.0, 0.0)):
            with NEContext(NEContext.Node, ed.NodeId(1)):
                imgui.text("Node 1")
                
                with NEContext(NEContext.Pin, ed.PinId(2), ed.PinKind.input):
                    imgui.text("In")
                imgui.same_line()
                with NEContext(NEContext.Pin, ed.PinId(3), ed.PinKind.output):
                    imgui.text("Out")
            
            with NEContext(NEContext.Node, ed.NodeId(4)):
                imgui.text("Node 2")
            
            with NEContext(NEContext.Creating):
                input_pin_id, output_pin_id = ed.PinId(), ed.PinId()
                if ed.query_new_link(input_pin_id, output_pin_id):
                    if input_pin_id and output_pin_id:
                        if ed.accept_new_item():
                            self.next_link_id += 1
                            ed.link(ed.LinkId(self.next_link_id), input_pin_id, output_pin_id)
        
        if self.gui_is_first_frame:
            ed.navigate_to_content(0.0)
            self.gui_is_first_frame = False

