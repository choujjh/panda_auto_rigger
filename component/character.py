import system.base_component as base_comp
import component.anim as anim
import component.misc as misc
import system.component_enum_data as component_enum_data

class CustomCharacter(base_comp.Character):
    def _override_build(self, **kwargs):
        pass

class SimpleCharacter(base_comp.Character):
    def _override_build(self, **kwargs):

        l_color = component_enum_data.Color.blue
        r_color = component_enum_data.Color.red
        setup_color = component_enum_data.Color.purple
        m_color = component_enum_data.Color.yellow

        l_char_side = component_enum_data.CharacterSide.left
        l_char_shader = self.get_color_shader(self._SETUP_COLOR, set_color=l_color)
        setup_shader = self.get_color_shader("setup", set_color=setup_color)
        l_leg_setup_inst = anim.SimpleLimbAnim.setup_component.create(
            instance_name="Leg", 
            parent=self, 
            control_color=setup_shader,
            hier_side=l_char_side)
        
        l_leg_anim = anim.SimpleLimbAnim.create(
            instance_name="Leg", 
            source_component=l_leg_setup_inst, 
            parent=self,
            control_color=l_char_shader,
            hier_side=l_char_side
        )

        l_hier_vis = misc.VisualizeHier.create(source_component=l_leg_anim, instance_name="L_Leg", parent=self)