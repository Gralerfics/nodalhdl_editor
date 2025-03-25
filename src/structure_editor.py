from nodalhdl.core.structure import Structure, Node

import sys
import weakref
from typing import Union, List, Tuple, Dict

from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore


class NEContext:
    class NEContextException(Exception): pass
    class NEContextSkipException(Exception): pass
    
    Editor = 0
    Node = 1
    Pin = 2
    OnCreate = 3
    OnDelete = 4
    QueryNewLink = 5
    
    def __init__(self, *arg, **kwargs):
        # properties for all contexts
        self.context_type = NEContext.Editor if "_context_type" not in kwargs else kwargs.pop("_context_type")
        self.arg = arg
        self.kwargs = kwargs
        
        # properties for Editor context
        self.id_counter = 0
        
        # properties for Node, Pin and Link contexts
        self.ctx: NEContext = None if "_context" not in kwargs else kwargs.pop("_context")
        self.id: Union[ed.NodeId, ed.PinId, ed.LinkId] = None
    
    def _reset_id(self):
        self.id_counter = 0
    
    def _next_id(self):
        self.id_counter += 1
        return self.id_counter
    
    def _trace(self, frame, event, arg):
        sys.settrace(None)
        raise NEContext.NEContextSkipException()
    
    def __enter__(self):
        def set_abort_hook():
            # https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block/12594789#12594789
            # https://github.com/rfk/withhacks
            sys.settrace(lambda *args, **keys: None)
            f = sys._getframe(0)
            while f.f_locals.get("self") is self:
                f = f.f_back
            f.f_trace = self._trace
        
        if self.context_type == NEContext.Editor: # id: str, size: ImVec2
            ed.begin(*self.arg, **self.kwargs)
            return self
        elif self.context_type == NEContext.Node: # id: NodeId
            self.id = ed.NodeId(self.ctx._next_id())
            ed.begin_node(self.id, *self.arg, **self.kwargs)
            return self
        elif self.context_type == NEContext.Pin: # id: PinId, kind: PinKind
            self.id = ed.PinId(self.ctx._next_id())
            ed.begin_pin(self.id, *self.arg, **self.kwargs)
            return self
        elif self.context_type == NEContext.OnCreate:
            if not ed.begin_create():
                set_abort_hook()
        elif self.context_type == NEContext.OnDelete:
            if not ed.begin_delete():
                set_abort_hook()
        elif self.context_type == NEContext.QueryNewLink:
            input_pin_id, output_pin_id = ed.PinId(), ed.PinId()
            if not ed.query_new_link(input_pin_id, output_pin_id):
                set_abort_hook()
            if not input_pin_id or not output_pin_id:
                set_abort_hook()
            return input_pin_id, output_pin_id
        else:
            raise NEContext.NEContextException("Invalid context type")
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is NEContext.NEContextSkipException:
            return True
        
        if self.context_type == NEContext.Editor:
            ed.end()
        elif self.context_type == NEContext.Node:
            ed.end_node()
        elif self.context_type == NEContext.Pin:
            ed.end_pin()
        elif self.context_type == NEContext.OnCreate:
            ed.end_create()
        elif self.context_type == NEContext.OnDelete:
            ed.end_delete()
        elif self.context_type == NEContext.QueryNewLink:
            pass
        else:
            raise NEContext.NEContextException("Invalid context type")
    
    def node(self):
        return NEContext(_context_type = NEContext.Node, _context = self)
    
    def pin(self, kind: ed.PinKind):
        return NEContext(kind = kind, _context_type = NEContext.Pin, _context = self)
    
    def link(self, start_pin_id: ed.PinId, end_pin_id: ed.PinId):
        l_id = ed.LinkId(self._next_id())
        ed.link(l_id, start_pin_id, end_pin_id)
        return l_id
    
    def onCreate(self):
        return NEContext(_context_type = NEContext.OnCreate)
    
    def onDelete(self):
        return NEContext(_context_type = NEContext.OnDelete)
    
    def queryNewLink(self):
        return NEContext(_context_type = NEContext.QueryNewLink)


class StructureEditor:
    def __init__(self, structure: Structure = None):
        # state
        self.structure: Structure = structure
        self.id_mapping: Dict[int, Union[Structure, Node]] = weakref.WeakValueDictionary()

        # editor
        ed_config = ed.Config()
        ed_config.settings_file = ""
        self.context: ed.EditorContext = ed.create_editor(ed_config)
        self.gui_is_first_frame = True
        
        # TODO
        self.m_HeaderBackground: imgui.ImTextureID
    
    def __del__(self):
        ed.destroy_editor(self.context)
    
    def gui(self):
        # node editor context
        if self.context is None:
            return
        ed.set_current_editor(self.context)
        
        # structure
        with NEContext("Editor") as ctx:
            if self.structure is None:
                return
            
            # TODO 遍历 ports_inside_flipped 绘制端口, 遍历 subs 绘制节点 (pin 对应相应 ports_outside), 遍历收集 net 绘制连线.
            
            
            # <For each node BEGIN>
            # builder.Begin
            ed.push_style_var(ed.StyleVar.node_padding, imgui.ImVec4(8, 4, 8, 8)) # builders.cpp: 34
            with ctx.node() as n: # builders.cpp: 36
                # imgui.push_id(n.id.id()) # builders.cpp: 38
                CurrentNodeId = n.id
                
                # <1> # blueprints-example.cpp: 947
                # builder.Header
                HeaderColor = imgui.ImColor(imgui.ImVec4(0.4, 0.4, 0.4, 1.0)) # builders.cpp: 96
                imgui.begin_horizontal("header") # builders.cpp: 237
                
                imgui.spring(0) # blueprints-example.cpp: 950
                imgui.text_unformatted("Node_name")
                imgui.spring(1)
                imgui.dummy(imgui.ImVec2(0, 28))
                if False: # TODO hasOutputDelegates
                    pass
                else:
                    imgui.spring(0) # blueprints-example.cpp: 990
                
                # builder.EndHeader
                imgui.end_horizontal() # builders.cpp: 176
                HeaderMin = imgui.get_item_rect_min() # builders.cpp: 177
                HeaderMax = imgui.get_item_rect_max() # builders.cpp: 178
                # imgui.spring(0, imgui.get_style().item_spacing.y * 2.0) # builders.cpp: 181
                # TODO builders.cpp: 240
                imgui.begin_horizontal("content") # builders.cpp: 244
                imgui.spring(0, 0)
                imgui.end_horizontal()
                
                # <2> # blueprints-example.cpp: 994
                # <For each in BEGIN>
                # alpha = imgui.get_style().alpha # blueprints-example.cpp: 996
                # alpha *= 48 / 255 # TODO
                
                # builder.Input(input_id)
                imgui.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0) # builders.cpp: 249
                ed.push_style_var(ed.StyleVar.pivot_alignment, imgui.ImVec2(0, 0.5))
                ed.push_style_var(ed.StyleVar.pivot_size, imgui.ImVec2(0, 0))
                # imgui.spring(0) # builders.cpp: 114
                with ctx.pin(ed.PinKind.input) as p: # builders.cpp: 117
                    imgui.begin_horizontal(p.id.id()) # builders.cpp: 119
                    
                    imgui.push_style_var(imgui.StyleVar_.alpha, 120) # alpha) # blueprints-example.cpp: 1001
                    # DrawPinIcon TODO
                    imgui.spring(0) # blueprints-example.cpp: 1003
                    if True: # blueprints-example.cpp: 1004
                        imgui.text_unformatted("Input_name")
                        imgui.spring(0)
                    # if Bool TODO
                    imgui.pop_style_var()
                    
                    # builder.EndInput
                    imgui.end_horizontal() # builders.cpp: 124
                ed.pop_style_var(2)
                imgui.spring(1, 0)
                imgui.end_vertical()
                
                # <For each in END>
                
                # <3> isSimple = True TODO
                
                # <4> # blueprints-example.cpp: 1027 TODO
                
                # builder.End
                # setstage end # builders.cpp: 46
            # builders.cpp: 48
            
            # TODO ImGui::IsItemVisible()
            drawList = ed.get_node_background_draw_list(CurrentNodeId)
            halfBorderWidth = ed.get_style().node_border_width * 0.5
            headerColor = imgui.IM_COL32(100, 100, 100, 120) # imgui.IM_COL32(0, 0, 0, 120) | (HeaderColor & imgui.IM_COL32(255, 255, 255, 0))
            
            
            if HeaderMax.x > HeaderMin.x and HeaderMax.y > HeaderMin.y:
                pass
            
            # imgui.pop_id()
            CurrentNodeId = 0
            ed.pop_style_var()
            
            # <For each node END>
            
            
            # with ctx.node() as n:
            #     imgui.text(f"Node {n.id.id()}")
                
            #     with ctx.pin(ed.PinKind.input) as p:
            #         imgui.text(f"In {p.id.id()}")
            #     imgui.same_line()
            #     with ctx.pin(ed.PinKind.output) as p:
            #         imgui.text(f"Out {p.id.id()}")
            
            # with ctx.node() as n:
            #     imgui.text(f"Node {n.id.id()}")
                
            #     with ctx.pin(ed.PinKind.input) as p:
            #         imgui.text(f"In {p.id.id()}")
            #     imgui.same_line()
            #     with ctx.pin(ed.PinKind.output) as p:
            #         imgui.text(f"Out {p.id.id()}")
            
            # with ctx.onCreate():
            #     with ctx.queryNewLink() as (input_pin_id, output_pin_id):
            #         if ed.accept_new_item():
            #             pass
        
        # locate
        if self.gui_is_first_frame:
            ed.navigate_to_content(0.0)
            self.gui_is_first_frame = False

