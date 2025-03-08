from typing import Dict, Callable

from imgui_bundle import hello_imgui, imgui, immapp, imgui_ctx # type: ignore
from imgui_bundle import icons_fontawesome_6
from imgui_bundle import ImVec4, ImVec2

from imgui_bundle import imgui_node_editor as ed # type: ignore
from imgui_bundle.demos_python import demo_utils

from state import StructureState


class DockingManager:
    def __init__(self):
        self.windows: Dict[str, hello_imgui.DockableWindow] = {}
    
    def add_window(self, label: str, gui_func: Callable, init_dockspace: str = None, include_in_view_menu: bool = True, remember_is_visible: bool = True, force_dockspace: bool = False):
        if label in self.windows.keys():
            raise Exception(f"Window \'{label}\' already exists")

        new_window = hello_imgui.DockableWindow()
        new_window.label = label
        new_window.include_in_view_menu = include_in_view_menu
        new_window.remember_is_visible = remember_is_visible
        new_window.dock_space_name = init_dockspace
        new_window.gui_function = gui_func
        
        self.windows[label] = new_window
        
        hello_imgui.add_dockable_window(new_window, force_dockspace = force_dockspace)
    
    def remove_window(self, label: str):
        if label not in self.windows.keys():
            raise Exception(f"Window \'{label}\' does not exist")
        
        hello_imgui.remove_dockable_window(label)
        
        del self.windows[label]


if __name__ == "__main__":
    docking_mgr = DockingManager()
    runner_params = hello_imgui.RunnerParams()
    
    # 主窗口
    runner_params.app_window_params.window_title = "NodalHDL Editor"
    runner_params.app_window_params.window_geometry.size = (1440, 900)
    runner_params.app_window_params.restore_previous_geometry = True
    
    # 状态栏
    runner_params.imgui_window_params.show_status_bar = True
    
    # 菜单栏
    runner_params.imgui_window_params.show_menu_bar = True
    runner_params.imgui_window_params.show_menu_app = False
    runner_params.imgui_window_params.show_menu_view = False
    runner_params.callbacks.show_menus = lambda: hello_imgui.show_view_menu(runner_params)
    
    # 默认分割
    split_main_bottom = hello_imgui.DockingSplit()
    split_main_bottom.initial_dock = "MainDockSpace"
    split_main_bottom.new_dock = "BottomSpace"
    split_main_bottom.direction = imgui.Dir.down
    split_main_bottom.ratio = 0.3

    split_main_left = hello_imgui.DockingSplit()
    split_main_left.initial_dock = "MainDockSpace"
    split_main_left.new_dock = "LeftSpace"
    split_main_left.direction = imgui.Dir.left
    split_main_left.ratio = 0.25

    split_main_right = hello_imgui.DockingSplit()
    split_main_right.initial_dock = "MainDockSpace"
    split_main_right.new_dock = "RightSpace"
    split_main_right.direction = imgui.Dir.right
    split_main_right.ratio = 0.25
    
    # 默认布局
    docking_params = hello_imgui.DockingParams()
    docking_params.layout_name = "Default"
    docking_params.docking_splits = [split_main_bottom, split_main_left, split_main_right]
    docking_params.dockable_windows = []
    
    # 启用
    runner_params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    runner_params.imgui_window_params.enable_viewports = True
    runner_params.docking_params = docking_params
    
    # 初始窗口
    docking_mgr.add_window("Logs", hello_imgui.log_gui, init_dockspace = "BottomSpace") # 日志
    
    # 配置文件 TODO
    runner_params.ini_folder_type = hello_imgui.IniFolderType.current_folder # hello_imgui.IniFolderType.app_user_config_folder
    runner_params.ini_filename = "editor.ini" # "nodalhdl_editor/editor.ini"
    
    # 启动
    hello_imgui.run(runner_params)
    
    # TODO 为了方便调试，暂时每次启动都清空配置文件
    import os
    if os.path.exists(runner_params.ini_filename):
        os.remove(runner_params.ini_filename)

