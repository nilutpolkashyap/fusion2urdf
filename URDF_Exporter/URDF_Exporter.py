#Author-syuntoku14
#Author-spacemaster85
#Author-nilutpolkashyap
#Modified on Sun Mar 17 2024
#Description-Generate URDF file from Fusion 360

import adsk, adsk.core, adsk.fusion, traceback
import os
import sys
import tkinter as tk
from tkinter import messagebox as mb
from .utils import utils
from .core import Link, Joint, Write

"""
# length unit is 'cm' and inertial unit is 'kg/cm^2'
# If there is no 'body' in the root component, maybe the corrdinates are wrong.
"""

# joint effort: 100
# joint velocity: 100
# supports "Revolute", "Rigid" and "Slider" joint types

# I'm not sure how prismatic joint acts if there is no limit in fusion model

def run(context):
    ui = None
    success_msg = 'URDF files generation cancelled'
    msg = success_msg

    try:
        # --------------------
        # initialize
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        title = 'Fusion2URDF'
        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        root = design.rootComponent  # root component 
        components = design.allComponents

        # set the names        
        robot_name = root.name.split()[0].lower()
        package_name = robot_name + '_description'
        save_dir = utils.file_dialog(ui)
        if save_dir == False:
            ui.messageBox('Fusion2URDF was canceled', title)
            return 0

        packagde_dir = save_dir
        output_msg = ' '
        
        appWin=tk.Tk()
        appWin.title("Choose your ROS Version")
        appWin.attributes('-toolwindow', True)
        appWin.geometry('300x150')

        ros_selection = tk.IntVar()
        def sel():
            appWin.destroy()
            appWin.quit()


        tk.Radiobutton(appWin, text="ROS 1",font=('Aerial', 14) ,indicatoron = 0, width = 150, height = 3, variable=ros_selection, value=1,
                  command=sel).pack()

        tk.Radiobutton(appWin, text="ROS 2",font=('Aerial', 14), indicatoron = 0, width = 150, height = 3, variable=ros_selection, value=2,
                  command=sel).pack()

        appWin.mainloop()
   
        save_dir= save_dir + '/' + package_name
        try: os.mkdir(save_dir)
        except: pass  


        package_dir_ros1 = os.path.abspath(os.path.dirname(__file__)) + '/package_ros1/'
        package_dir_ros2 = os.path.abspath(os.path.dirname(__file__)) + '/package_ros2/'        
        # --------------------
        # set dictionaries
        
        # Generate joints_dict. All joints are related to root. 
        joints_dict, msg = Joint.make_joints_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0   
        print(joints_dict)
        # Generate inertial_dict
        inertial_dict, msg = Link.make_inertial_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0
        elif not 'base_link' in inertial_dict:
            msg = 'There is no base_link. Please set base_link and run again.'
            ui.messageBox(msg, title)
            return 0
        
        material_dict, color_dict, msg = Link.make_material_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0  
        
        links_xyz_dict = {} 
        # --------------------
        # Generate URDF
        Write.write_urdf(joints_dict, links_xyz_dict, inertial_dict, material_dict, package_name, robot_name, save_dir, ros_selection.get() != 2)
        Write.write_materials_xacro(color_dict, robot_name, save_dir)
        Write.write_transmissions_xacro(joints_dict, links_xyz_dict, robot_name, save_dir)

        # Generate ROS 1 packages
        if (ros_selection.get() == 1):
            utils.copy_package(save_dir, package_dir_ros1)
            utils.update_cmakelists(save_dir, robot_name)
            utils.update_package_xml(save_dir, robot_name)

            Write.write_gazebo_xacro(joints_dict, links_xyz_dict, inertial_dict, package_name, robot_name, save_dir)
 
            utils.update_ros1_display_launch(save_dir, robot_name)
            utils.update_ros1_gazebo_launch(save_dir, robot_name)

        else:
            utils.copy_package(save_dir, package_dir_ros2)
            utils.update_cmakelists(save_dir, robot_name)
            utils.update_package_xml(save_dir, robot_name)
            
            Write.write_gazebo_xacro(joints_dict, links_xyz_dict, inertial_dict, package_name, robot_name, save_dir)
            Write.write_display_launch(package_name, robot_name, save_dir)
            Write.write_gazebo_launch(package_name, robot_name, save_dir)
            Write.write_control_launch(package_name, robot_name, save_dir, joints_dict)
            Write.write_yaml(package_name, robot_name, save_dir, joints_dict)
 
            # utils.copy_package(save_dir, package_dir_ros1)
            # utils.update_cmakelists(save_dir, package_name)
            # utils.update_package_xml(save_dir, package_name)

        # Generate STl files        
        utils.export_stl(app, save_dir)   

        ui.messageBox(msg, title)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
