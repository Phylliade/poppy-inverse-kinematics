import unittest
import numpy as np
import sys
from ikpy import chain
from ikpy import plot_utils
from ikpy import matrix_link
import sympy
import params

import json
import subprocess

plot = params.interactive


class TestChain(unittest.TestCase):
    def setUp(self):
        if plot:
            self.ax = plot_utils.init_3d_figure()
        self.chain1 = chain.Chain.from_urdf_file(params.resources_path + "/poppy_torso.URDF", base_elements=["base", "abs_z", "spine", "bust_y", "bust_motors", "bust_x", "chest", "r_shoulder_y"], last_link_vector=[0, 0.18, 0], active_links_mask=[False, False, False, True, True, True, True, True])
        self.joints = [0] * self.chain1.get_num_params()
        self.joints[-4] = 0
        self.target = [0.1, -0.2, 0.1]
        self.frame_target = np.eye(4)
        self.frame_target[:3, 3] = self.target

    def test_chain(self):
        self.chain1 = chain.Chain.from_urdf_file(params.resources_path + "/poppy_torso.URDF", base_elements=["base", "abs_z", "spine", "bust_y", "bust_motors", "bust_x", "chest", "r_shoulder_y"], last_link_vector=[0, 0.18, 0], active_links_mask=[False, False, False, True, True, True, True, True])
        self.chain2 = chain.Chain.from_urdf_file(params.resources_path + "/poppy_torso.URDF", base_elements=["base", "abs_z", "spine", "bust_y", "bust_motors", "bust_x", "chest", "l_shoulder_y"], last_link_vector=[0, 0.18, 0], active_links_mask=[False, False, False, True, True, True, True, True])
        
        if plot:
            self.chain1.plot(self.joints, self.ax)
            self.chain2.plot(self.joints, self.ax)

    def test_ik(self):

        ik = self.chain1.inverse_kinematics(self.frame_target, initial_position=self.joints)

        if plot:
            self.chain1.plot(ik, self.ax, target=self.target)
            plot_utils.show_figure()

        np.testing.assert_almost_equal(self.chain1.forward_kinematics(ik)[:3, 3], self.target, decimal=3)

    def test_ik_optimization(self):
        """Tests the IK optimization-based method"""
        args = {"max_iter": 3}
        ik = self.chain1.inverse_kinematics(self.frame_target, initial_position=self.joints, **args)
        # Check whether the results are almost equal
        np.testing.assert_almost_equal(self.chain1.forward_kinematics(ik)[:3, 3], self.target, decimal=1)

    def test_matrix(self):
        x = sympy.Symbol("x")
        y = sympy.Symbol("y")
        l1 = matrix_link.VariableMatrixLink("r1", None, [[sympy.cos(x),-sympy.sin(x),0,0],[sympy.sin(x),sympy.cos(x),0,0],[0,0,1,0],[0,0,0,1]], [x, y])
        l2 = matrix_link.ConstantMatrixLink("test", "r1", [[10],[0],[0],[1]])
        c = chain.Chain([l1, l2], [True, False])
        args = {"max_iter": 100}
        target_matrix = np.eye(4)
        target = [0,10,0]
        target_matrix[:3,3] = target
        ik = c.inverse_kinematics(target_matrix, [3.1415, 0], **args)
        np.testing.assert_almost_equal(c.forward_kinematics(ik)[:3, 0], target, decimal=1)
        if plot:
            c.plot(ik, self.ax)
            plot_utils.show_figure()

    def test_blender(self):
        blend_path = "../../resources/buggybot.blend"
        python_script = "../../scripts/blender/blender_export.py"
        command = ["blender", blend_path, "--background", "--python", python_script]
        out = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
        data = False
        out_data = []
        for l in out.split("\n"):
            if l == "end_data":
                data = False
            if data:
                out_data.append(l)
            if l == "begin_data":
                data = True
        json_links_list = json.loads("\n".join(out_data))
        json_links_dict = {}
        for l in json_links_list:
            json_links_dict[l["name"]] = l
        endpoint = "armature/forearm_right_back/endpoint"
        links_list = []
        while endpoint != None:
            json_link = json_links_dict[endpoint]
            if json_link["is_variable"]:
                link = matrix_link.VariableMatrixLink(json_link["name"], json_link["parent"], json_link["matrix"], [sympy.Symbol("x")])
                links_list = [link] + links_list
            else:
                link = matrix_link.ConstantMatrixLink(json_link["name"], json_link["parent"], json_link["matrix"])
                links_list = [link] + links_list
            endpoint = json_link["parent"]
        c = chain.Chain(links_list, [True, True, True])
        target_matrix = np.eye(4)
        target = [-100,-100,-100]
        target_matrix[:3,3] = target
        args = {"max_iter": 1000}
        ik = c.inverse_kinematics(target_matrix, [0,0,3.1415/2], **args)
        if plot:
            c.plot(ik, self.ax)
            plot_utils.show_figure()

if __name__ == '__main__':
    unittest.main(verbosity=2, argv=[sys.argv[0]])
