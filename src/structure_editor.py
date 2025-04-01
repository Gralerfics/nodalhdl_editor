from nodalhdl.core.structure import Structure, Net, Node
from nodalhdl.core.signal import Input, Output

import sys
import weakref
from typing import Union, List, Tuple, Dict, Set

from imgui_bundle import imgui, imgui_ctx, imgui_node_editor as ed # type: ignore
import ed_ctx


class StructureEditor:
    def __init__(self, structure: Structure = None):
        # state
        self.structure: Structure = structure

        # editor
        ed_config = ed.Config()
        ed_config.settings_file = ""
        self.context: ed.EditorContext = ed.create_editor(ed_config)
        self.gui_is_first_frame = True
    
    def __del__(self):
        ed.destroy_editor(self.context)
    
    def gui(self):
        # node editor context
        if self.context is None:
            return
        ed.set_current_editor(self.context)
        
        # structure
        with ed_ctx.editor(f"editor_{hash(self)}") as ctx:
            with imgui_ctx.push_id(f"editor_{ctx.editor_id}"):
                if self.structure is None:
                    return
                
                id_obj_mapping: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
                obj_id_mapping: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
                nets: weakref.WeakSet[Net] = weakref.WeakSet()
                
                # draw IOs as non-header ed nodes
                for port_full_name, port in self.structure.ports_inside_flipped.nodes():
                    nets.add(port.located_net)
                    
                    with ed_ctx.style_var([
                        (ed.StyleVar.node_padding, imgui.ImVec4(8, 4, 8, 8)),
                        (ed.StyleVar.node_rounding, 8)
                    ]):
                        # ed node
                        with ed_ctx.node(ctx) as n:
                            with imgui_ctx.push_id(f"io_{n.node_id.id()}"):
                                # panel
                                with imgui_ctx.begin_vertical("panel"):
                                    # io
                                    with ed_ctx.style_var([
                                        (ed.StyleVar.pivot_alignment, imgui.ImVec2(0, 0.5)),
                                        (ed.StyleVar.pivot_size, imgui.ImVec2(0, 0))
                                    ]):
                                        imgui.text_unformatted("io")
                                        text_rect_min = imgui.get_item_rect_min()
                                        text_rect_max = imgui.get_item_rect_max()
                                        
                                        with imgui_ctx.begin_horizontal("io"):
                                            imgui.spring(0, 0)
                                            
                                            if port.origin_signal_type.belongs(Output):
                                                imgui.spring(1, 0)
                                            
                                            with ed_ctx.pin(ctx, ed.PinKind.input if port.origin_signal_type.belongs(Input) else ed.PinKind.output) as p:
                                                id_obj_mapping[p.pin_id] = port
                                                obj_id_mapping[port] = p.pin_id
                                                
                                                with imgui_ctx.begin_horizontal(p.pin_id.id()):
                                                    with imgui_ctx.push_style_var(imgui.StyleVar_.alpha, 120):
                                                        # DrawPinIcon TODO
                                                        imgui.text_unformatted(port_full_name)
                                                        imgui.spring(0)
                                
                                panel_rect_min = imgui.get_item_rect_min()
                                panel_rect_max = imgui.get_item_rect_max()
                        
                        # draw node background
                        header_rect_min = panel_rect_min
                        header_rect_max = imgui.ImVec2(panel_rect_max.x, text_rect_max.y + 1)
                        
                        node_bkg_draw_list = ed.get_node_background_draw_list(n.node_id)
                        half_border_width = ed.get_style().node_border_width * 0.5
                        header_color = imgui.IM_COL32(100, 100, 100, 120) # imgui.IM_COL32(0, 0, 0, 120) | (HeaderColor & imgui.IM_COL32(255, 255, 255, 0))
                        
                        if header_rect_max.x > header_rect_min.x and header_rect_max.y > header_rect_min.y:
                            node_bkg_draw_list.add_rect_filled(
                                header_rect_min - imgui.ImVec2(8 - half_border_width, 4 - half_border_width),
                                header_rect_max + imgui.ImVec2(8 - half_border_width, 0),
                                header_color,
                                ed.get_style().node_rounding,
                                imgui.ImDrawFlags_.round_corners_top
                            )
                
                # draw substructures as ed nodes
                for subs_inst_name, subs in self.structure.substructures.items():
                    with ed_ctx.style_var([
                        (ed.StyleVar.node_padding, imgui.ImVec4(8, 4, 8, 8)),
                        (ed.StyleVar.node_rounding, 8)
                    ]):
                        # ed node
                        with ed_ctx.node(ctx) as n:
                            id_obj_mapping[n.node_id] = subs
                            obj_id_mapping[subs] = n.node_id
                            
                            with imgui_ctx.push_id(f"node_{n.node_id.id()}"):
                                # panel
                                with imgui_ctx.begin_vertical("panel"):
                                    # header
                                    with imgui_ctx.begin_horizontal("header"):
                                        imgui.spring(0)
                                        imgui.text_unformatted(subs_inst_name)
                                        imgui.spring(1)
                                        imgui.dummy(imgui.ImVec2(0, 28))
                                        imgui.spring(0)
                                    
                                    header_rect_min = imgui.get_item_rect_min()
                                    header_rect_max = imgui.get_item_rect_max()
                                    
                                    # ImGui::Spring(0, ImGui::GetStyle().ItemSpacing.y * 2.0f);
                                    
                                    # content
                                    with imgui_ctx.begin_horizontal("content"):
                                        imgui.spring(0, 0)
                                        
                                        # input pins
                                        with imgui_ctx.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0):
                                            with ed_ctx.style_var([
                                                (ed.StyleVar.pivot_alignment, imgui.ImVec2(0, 0.5)),
                                                (ed.StyleVar.pivot_size, imgui.ImVec2(0, 0))
                                            ]):
                                                for port_full_name, port in subs.ports_outside[(self.structure.id, subs_inst_name)].nodes():
                                                    if not port.origin_signal_type.belongs(Input):
                                                        continue
                                                    
                                                    nets.add(port.located_net)
                                                    
                                                    imgui.spring(0)
                                                    with ed_ctx.pin(ctx, ed.PinKind.input) as p:
                                                        id_obj_mapping[p.pin_id] = port
                                                        obj_id_mapping[port] = p.pin_id
                                                        
                                                        with imgui_ctx.begin_horizontal(p.pin_id.id()):
                                                            with imgui_ctx.push_style_var(imgui.StyleVar_.alpha, 120):
                                                                # DrawPinIcon TODO
                                                                imgui.text_unformatted(port_full_name)
                                                                imgui.spring(0)
                                            imgui.spring(1, 0)
                                        
                                        imgui.spring(1)
                                        
                                        # output pins
                                        with imgui_ctx.begin_vertical("outputs", imgui.ImVec2(0, 0), 0.0):
                                            with ed_ctx.style_var([
                                                (ed.StyleVar.pivot_alignment, imgui.ImVec2(1, 0.5)),
                                                (ed.StyleVar.pivot_size, imgui.ImVec2(0, 0))
                                            ]):
                                                for port_full_name, port in subs.ports_outside[(self.structure.id, subs_inst_name)].nodes():
                                                    if not port.origin_signal_type.belongs(Output):
                                                        continue
                                                    
                                                    nets.add(port.located_net)
                                                    
                                                    imgui.spring(0)
                                                    with ed_ctx.pin(ctx, ed.PinKind.output) as p:
                                                        id_obj_mapping[p.pin_id] = port
                                                        obj_id_mapping[port] = p.pin_id
                                                        
                                                        with imgui_ctx.begin_horizontal(p.pin_id.id()):
                                                            with imgui_ctx.push_style_var(imgui.StyleVar_.alpha, 120):
                                                                # DrawPinIcon TODO
                                                                imgui.text_unformatted(port_full_name)
                                                                imgui.spring(0)
                                            imgui.spring(1, 0)
                                    
                                    content_rect_min = imgui.get_item_rect_min()
                                    content_rect_max = imgui.get_item_rect_max()
                                
                                panel_rect_min = imgui.get_item_rect_min()
                                panel_rect_max = imgui.get_item_rect_max()
                        
                        # draw node background
                        node_bkg_draw_list = ed.get_node_background_draw_list(n.node_id)
                        half_border_width = ed.get_style().node_border_width * 0.5
                        header_color = imgui.IM_COL32(100, 100, 100, 120) # imgui.IM_COL32(0, 0, 0, 120) | (HeaderColor & imgui.IM_COL32(255, 255, 255, 0))
                        
                        if header_rect_max.x > header_rect_min.x and header_rect_max.y > header_rect_min.y:
                            node_bkg_draw_list.add_rect_filled(
                                header_rect_min - imgui.ImVec2(8 - half_border_width, 4 - half_border_width),
                                header_rect_max + imgui.ImVec2(8 - half_border_width, 0),
                                header_color,
                                ed.get_style().node_rounding,
                                imgui.ImDrawFlags_.round_corners_top
                            )
                
                # draw nets
                for net in nets:
                    driver_pin_id = obj_id_mapping.get(net.driver())
                    if driver_pin_id is None:
                        continue
                    
                    for node in net.nodes_weak:
                        node_pin_id = obj_id_mapping.get(node)
                        if node_pin_id is None or node_pin_id is driver_pin_id:
                            continue
                        
                        ed_ctx.link(ctx, driver_pin_id, node_pin_id)
                
                # link on_create
                with ed_ctx.on_create():
                    with ed_ctx.new_link() as (input_pin_id, output_pin_id):
                        if ed.accept_new_item():
                            pass
        
        # locate
        if self.gui_is_first_frame:
            ed.navigate_to_content(0.0)
            self.gui_is_first_frame = False

