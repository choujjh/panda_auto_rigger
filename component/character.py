import system.base_component as base_comp
import component.anim as anim
import component.setup as setup
import system.component_enum_data as component_enum_data

class CustomCharacter(base_comp.Character):
    def _override_build(self, **kwargs):
        pass

class SimpleCharacter(base_comp.Character):
    def _override_build(self, **kwargs):

        l_color = component_enum_data.Color.blue
        l_char_side = component_enum_data.CharacterSide.left
        l_char_shader = self.get_color_shader(l_char_side, set_color=l_color)
        
        l_leg_anim_inst = anim.SimpleLimbAnim.create(
            instance_name="Leg", 
            parent=self, 
            control_color=l_char_shader,
            setup_color=self.get_color_shader(self._SETUP_CLR),
            hier_side=l_char_side)