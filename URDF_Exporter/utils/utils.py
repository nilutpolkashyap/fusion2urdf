# -*- coding: utf-8 -*-
"""
Created on Sun May 12 19:15:34 2019
Modified on Thu Mar 21 2024

@author: syuntoku
@author: spacemaster85
@author: nilutpolkashyap
"""

import adsk
import adsk.core
import adsk.fusion
import os.path
import re
from xml.etree import ElementTree
from xml.dom import minidom
from distutils.dir_util import copy_tree
import fileinput
import sys


def export_stl(_app, save_dir):
    """
    export stl files into "sace_dir/"


    Parameters
    ----------
    _app: adsk.core.Application.get()
    save_dir: str
        directory path to save
    """

    def traverse( occ):
    # recursive method to get all bodies from components and sub-components
        body = adsk.fusion.BRepBody.cast(None)
        liste = []
        if occ.childOccurrences and occ.isLightBulbOn:
            for child in occ.childOccurrences:
                liste = liste + traverse(child)
        if occ.isLightBulbOn:   
            liste = liste + [body for body in occ.bRepBodies if body.isLightBulbOn and occ.component.isBodiesFolderLightBulbOn]
        return liste


    des: adsk.fusion.Design = _app.activeProduct
    root: adsk.fusion.Component = des.rootComponent

    showBodies = []
    body = adsk.fusion.BRepBody.cast(None)
    if root.isBodiesFolderLightBulbOn:
        lst = [body for body in root.bRepBodies if body.isLightBulbOn]
        if len(lst) > 0:
            showBodies.append(['root', lst])

        occ = adsk.fusion.Occurrence.cast(None)
        for occ in root.allOccurrences:
            if not occ.assemblyContext and occ.isLightBulbOn:
                lst = [body for body in occ.bRepBodies if body.isLightBulbOn and occ.component.isBodiesFolderLightBulbOn]
                if occ.childOccurrences:
                    for child in occ.childOccurrences:
                        lst = lst + traverse(child)
                if len(lst) > 0:
                    showBodies.append([occ.name, lst])

        # get clone body
        tmpBrepMng = adsk.fusion.TemporaryBRepManager.get()
        tmpBodies = []
        for name, bodies in showBodies:
            lst = [tmpBrepMng.copy(body) for body in bodies]
            if len(lst) > 0:
                tmpBodies.append([name, lst])

        # create export Doc - DirectDesign
        fusionDocType = adsk.core.DocumentTypes.FusionDesignDocumentType
        expDoc: adsk.fusion.FusionDocument = _app.documents.add(fusionDocType)
        expDes: adsk.fusion.Design = expDoc.design
        expDes.designType = adsk.fusion.DesignTypes.DirectDesignType

        # get export rootComponent
        expRoot: adsk.fusion.Component = expDes.rootComponent

        # paste clone body
        mat0 = adsk.core.Matrix3D.create()
        for name, bodies in tmpBodies:
            occ = expRoot.occurrences.addNewComponent(mat0)
            comp = occ.component
            comp.name = name
            for body in bodies:
                comp.bRepBodies.add(body)

        # export stl
        try:
            os.mkdir(save_dir + '/meshes')
        except:
            pass
        exportFolder = save_dir + '/meshes'

        exportMgr = des.exportManager
        for occ in expRoot.allOccurrences:
            if "base_link" in occ.component.name:
                expName = "base_link"
            else:
                expName = re.sub('[ :()]', '_', occ.component.name)
            expPath = os.path.join(exportFolder, '{}.stl'.format(expName))
            stlOpts = exportMgr.createSTLExportOptions(occ, expPath)
            exportMgr.execute(stlOpts)

        # remove export Doc
        expDoc.close(False)

def file_dialog(ui):
    """
    display the dialog to save the file
    """
    # Set styles of folder dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Fusion Folder Dialog'

    # Show folder dialog
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return folderDlg.folder
    return False

def origin2center_of_mass(inertia, center_of_mass, mass):
    """
    convert the moment of the inertia about the world coordinate into
    that about center of mass coordinate


    Parameters
    ----------
    moment of inertia about the world coordinate:  [xx, yy, zz, xy, yz, xz]
    center_of_mass: [x, y, z]


    Returns
    ----------
    moment of inertia about center of mass : [xx, yy, zz, xy, yz, xz]
    """
    x = center_of_mass[0]
    y = center_of_mass[1]
    z = center_of_mass[2]
    translation_matrix = [y**2+z**2, x**2+z**2, x**2+y**2,
                          -x*y, -y*z, -x*z]
    return [round(i - mass*t, 6) for i, t in zip(inertia, translation_matrix)]

def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.
    Parameters
    ----------
    elem : xml.etree.ElementTree.Element


    Returns
    ----------
    pretified xml : str
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def copy_package(save_dir, package_dir):
    """
    copies the directories and their contents from the template packages
    ["launch", "config", "urdf", "worlds"]   

    Parameter
    ---------
    packagde_dir: str
        path of template package
    save_dir: str
        path of the repository to save
    """
    try:
        os.mkdir(save_dir + '/launch')
    except:
        pass
    try:
        os.mkdir(save_dir + '/config')
    except:
        pass
    try:
        os.mkdir(save_dir + '/urdf')
    except:
        pass
    try:
        os.mkdir(save_dir + '/worlds')
    except:
        pass
    copy_tree(package_dir, save_dir)

def update_cmakelists(save_dir, robot_name):
    """
    update ros CMakeLists.txt file "save_dir/CMakeLists.txt"
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/CMakeLists.txt'

    for line in fileinput.input(file_name, inplace=True):
        if 'project(fusion2urdf_description)' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_package_xml(save_dir, robot_name):
    """
    update ros package.xml file "save_dir/package.xml"
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/package.xml'

    for line in fileinput.input(file_name, inplace=True):
        if '<name>' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        elif '<description>' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_ros1_display_launch(save_dir, robot_name):
    """
    update ros 1 display launch file "save_dir/launch/display.launch"
    displays robot urdf in Rviz
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/launch/display.launch'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_ros1_gazebo_launch(save_dir, robot_name):
    """
    update ros 1 gazebo classic launch file "save_dir/launch/gazebo.launch"
    spawns robot urdf in gazebo classic
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/launch/gazebo.launch'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_ros2_display_launch(save_dir, robot_name):
    """
    update ros 2 display launch file "save_dir/launch/display.launch.py"
    displays robot urdf in Rviz
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/launch/display.launch.py'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_ros2_gazebo_launch(save_dir, robot_name):
    """
    update ros 1 gazebo classic launch file "save_dir/launch/gazebo.launch.py"
    spawns robot urdf in gazebo classic
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/launch/gazebo.launch.py'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)

def update_ros2_gz_sim_launch(save_dir, robot_name):
    """
    update ros 2 gazebo sim launch file "save_dir/launch/gz-sim.launch.py"
    spawns robot urdf in gazebo sim (previously ignition)
    
    Parameter
    ---------
    robot_name: str
        name of the robot
    save_dir: str
        path of the repository to save
    """
    file_name = save_dir + '/launch/gz-sim.launch.py'

    for line in fileinput.input(file_name, inplace=True):
        if 'fusion2urdf' in line:
            sys.stdout.write(line.replace('fusion2urdf', robot_name))
        else:
            sys.stdout.write(line)