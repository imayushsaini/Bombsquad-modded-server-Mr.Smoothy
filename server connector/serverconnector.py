

# ba_meta require api 6

""" Easy to use new server connector  by Mr.Smoothy 
@mr.smoothy#5824
https://discord.gg/VJPf9hsEzb

"""
from __future__ import annotations
import copy
import time
from typing import TYPE_CHECKING, cast
import os
import _ba
import ba
import time
import threading
from enum import Enum
from bastd.ui.gather.bases import GatherTab
from dataclasses import dataclass
if TYPE_CHECKING:
    from typing import Any, Optional, Dict, List, Tuple,Type
    import ba
    
from bastd.ui.gather import GatherWindow
from bastd.ui.confirm import ConfirmWindow
import bastd.ui.gather as gt



def _safe_set_text(txt: Optional[ba.Widget],
                   val: Union[str, ba.Lstr],
                   success: bool = True) -> None:
    if txt:
        ba.textwidget(edit=txt,
                      text=val,
                      color=(0, 1, 0) if success else (1, 1, 0))


class _HostLookupThread(threading.Thread):
    """Thread to fetch an addr."""

    def __init__(self, name: str, port: int,
                 call: Callable[[Optional[str], int], Any]):
        super().__init__()
        self._name = name
        self._port = port
        self._call = call

    def run(self) -> None:
        result: Optional[str]
        try:
            import socket
            result = socket.gethostbyname(self._name)
        except Exception:
            result = None
        ba.pushcall(lambda: self._call(result, self._port),
                    from_other_thread=True)

class SubTabType(Enum):
    """Available sub-tabs."""
    NEW = 'new'
    SAVED = 'saved'

@dataclass
class State:
    """State saved/restored only while the app is running."""
    sub_tab: SubTabType = SubTabType.NEW
    parties: Optional[List[Tuple[str, PartyEntry]]] = None
    next_entry_index: int = 0
    filter_value: str = ''
    have_server_list_response: bool = False
    have_valid_server_list: bool = False


class newManualGatherTab(GatherTab):
    """The manual tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._check_button: Optional[ba.Widget] = None
        self._doing_access_check: Optional[bool] = None
        self._access_check_count: Optional[int] = None
        self._sub_tab: SubTabType = SubTabType.SAVED
        self._t_addr: Optional[ba.Widget] = None
        self._t_accessible: Optional[ba.Widget] = None
        self._t_accessible_extra: Optional[ba.Widget] = None
        self._access_check_timer: Optional[ba.Timer] = None
        self._checking_state_text: Optional[ba.Widget] = None
        self._container: Optional[ba.Widget] = None

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:

        c_width = region_width
        c_height = region_height - 20
        last_addr = ba.app.config.get('Last Manual Party Connect Address', '')

        self._container = ba.containerwidget(
            parent=parent_widget,
            position=(region_left,
                      region_bottom + (region_height - c_height) * 0.5),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True)
        v = c_height - 30
        self._join_new_party_text = ba.textwidget(
            parent=self._container,
            position=(c_width * 0.5 - 245, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='left',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.NEW,
                region_width,
                region_height,
                playsound=True,
            ),
            text="Join By Address")
        self._join_saved_party_text = ba.textwidget(
            parent=self._container,
            position=(c_width * 0.5 + 45, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='left',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.SAVED,
                region_width,
                region_height,
                playsound=True,
            ),
            text="Join Saved Party")
        ba.widget(edit=self._join_new_party_text, up_widget=tab_button)
        ba.widget(edit=self._join_saved_party_text,
                  left_widget=self._join_new_party_text,
                  up_widget=tab_button)
        ba.widget(edit=self._join_new_party_text, right_widget=self._join_saved_party_text)
        self._set_sub_tab(self._sub_tab, region_width, region_height)
     
        
        return self._container
    def save_state(self) -> None:
      ba.app.ui.window_states[self.__class__.__name__] = State(
            sub_tab=self._sub_tab
            )
    def restore_state(self) -> None:
        state = ba.app.ui.window_states.get(self.__class__.__name__)
        if state is None:
            state = State()
        assert isinstance(state, State)
        self._sub_tab = state.sub_tab
    def _set_sub_tab(self,
                     value: SubTabType,
                     region_width: float,
                     region_height: float,
                     playsound: bool = False) -> None:
        assert self._container
        if playsound:
            ba.playsound(ba.getsound('click01'))

        # Reset our selection.
        # (prevents selecting something way down the list if we switched away
        # and came back)
        self._selection = None
        self._have_user_selected_row = False

        # Reset refresh to the top and make sure everything refreshes.
        self._refresh_ui_row = 0
        

        self._sub_tab = value
        active_color = (0.6, 1.0, 0.6)
        inactive_color = (0.5, 0.4, 0.5)
        ba.textwidget(
            edit=self._join_new_party_text,
            color=active_color if value is SubTabType.NEW else inactive_color)
        ba.textwidget(
            edit=self._join_saved_party_text,
            color=active_color if value is SubTabType.SAVED else inactive_color)

        # Clear anything existing in the old sub-tab.
        for widget in self._container.get_children():
            if widget and widget not in {self._join_saved_party_text, self._join_new_party_text}:
                widget.delete()

        if value is SubTabType.NEW:
            self._build_new_party_tab(region_width, region_height)

        if value is SubTabType.SAVED:
            self._build_saved_party_tab(region_width, region_height)
    # The old manual tab
    def _build_new_party_tab(self, region_width: float,
                        region_height: float) -> None:
        c_width = region_width
        c_height = region_height -20
        last_addr = ba.app.config.get('Last Manual Party Connect Address', '')
        v = c_height - 100
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.3,
                      size=(0, 0),
                      maxwidth=c_width * 0.9,
                      h_align='center',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualDescriptionText'))
        v -= 30
        v -= 70
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5 - 260 - 50, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.0,
                      size=(0, 0),
                      maxwidth=130,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualAddressText'))
        txt = ba.textwidget(parent=self._container,
                            editable=True,
                            description=ba.Lstr(resource='gatherWindow.'
                                                'manualAddressText'),
                            position=(c_width * 0.5 - 240 - 50, v - 30),
                            text=last_addr,
                            autoselect=True,
                            v_align='center',
                            scale=1.0,
                            size=(420, 60))
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5 - 260 + 490, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.0,
                      size=(0, 0),
                      maxwidth=80,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'portText'))
        txt2 = ba.textwidget(parent=self._container,
                             editable=True,
                             description=ba.Lstr(resource='gatherWindow.'
                                                 'portText'),
                             text='43210',
                             autoselect=True,
                             max_chars=5,
                             position=(c_width * 0.5 - 240 + 490, v - 30),
                             v_align='center',
                             scale=1.0,
                             size=(170, 60))

        v -= 110

        btn = ba.buttonwidget(parent=self._container,
                              size=(300, 70),
                              label=ba.Lstr(resource='gatherWindow.'
                                            'manualConnectText'),
                              position=(c_width * 0.5 - 300 , v),
                              autoselect=True,
                              on_activate_call=ba.Call(self._connect, txt,
                                                       txt2))
        btn2 = ba.buttonwidget(parent=self._container,
                              size=(300, 70),
                              label="Save",
                              position=(c_width * 0.5 - 240 + 490 - 200 , v),
                              autoselect=True,
                              on_activate_call=ba.Call(self._save_server, txt,
                                                       txt2))
        # ba.widget(edit=txt, up_widget=tab_button)
        ba.textwidget(edit=txt, on_return_press_call=btn.activate)
        ba.textwidget(edit=txt2, on_return_press_call=btn.activate)
        v -= 45

        self._check_button = ba.textwidget(
            parent=self._container,
            size=(250, 60),
            text=ba.Lstr(resource='gatherWindow.'
                         'showMyAddressText'),
            v_align='center',
            h_align='center',
            click_activate=True,
            position=(c_width * 0.5 - 125, v - 30),
            autoselect=True,
            color=(0.5, 0.9, 0.5),
            scale=0.8,
            selectable=True,
            on_activate_call=ba.Call(self._on_show_my_address_button_press, v,
                                     self._container, c_width))
        
    # Tab containing saved parties
    def _build_saved_party_tab(self, region_width: float,
                        region_height: float) -> None:
        c_width = region_width
        c_height = region_height - 20
        v = c_height - 35
        v -= 25
        is_public_enabled = _ba.get_public_party_enabled()
        v -= 30
        uiscale = ba.app.ui.uiscale
        self._width = 1240 if uiscale is ba.UIScale.SMALL else 1040
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (578 if uiscale is ba.UIScale.SMALL else
                        670 if uiscale is ba.UIScale.MEDIUM else 800)
        scroll_buffer_h = 130 + 2 * x_inset
        tab_buffer_h = 750 + 2 * x_inset
        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        
        if True:
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            sub_scroll_height = c_height - 63
            self._my_parties_scroll_width = sub_scroll_width = (
                680 if uiscale is ba.UIScale.SMALL else 640)

           

            v = c_height - 30
            
            b_width = 140 if uiscale is ba.UIScale.SMALL else 178
            b_height = (107 if uiscale is ba.UIScale.SMALL else
                        142 if uiscale is ba.UIScale.MEDIUM else 190)
            b_space_extra = (0 if uiscale is ba.UIScale.SMALL else
                             -2 if uiscale is ba.UIScale.MEDIUM else -5)

            b_color = (0.6, 0.53, 0.63)
            b_textcolor = (0.75, 0.7, 0.8)
            btnv = (c_height - (48 if uiscale is ba.UIScale.SMALL else
                                45 if uiscale is ba.UIScale.MEDIUM else 40) -
                    b_height)
            btnh = 40 if uiscale is ba.UIScale.SMALL else 40
            smlh = 190 if uiscale is ba.UIScale.SMALL else 225
            tscl = 1.0 if uiscale is ba.UIScale.SMALL else 1.2
            self._my_saved_party_connect_button = btn1 = ba.buttonwidget(
                parent=self._container,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_saved_party_press,
                text_scale=tscl,
                label="Connect",
                autoselect=True)
            # ba.widget(edit=btn1, up_widget=self._tab_row.tabs[tab_id].button)
            if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
                ba.widget(edit=btn1,
                          left_widget=_ba.get_special_widget('back_button'))
            btnv -= b_height + b_space_extra
            ba.buttonwidget(parent=self._container,
                            size=(b_width, b_height),
                            position=(btnh, btnv),
                            button_type='square',
                            color=b_color,
                            textcolor=b_textcolor,
                            on_activate_call=self._on_my_saved_party_rename_press,
                            text_scale=tscl,
                            label="Rename",
                            autoselect=True)
            btnv -= b_height + b_space_extra
            ba.buttonwidget(parent=self._container,
                            size=(b_width, b_height),
                            position=(btnh, btnv),
                            button_type='square',
                            color=b_color,
                            textcolor=b_textcolor,
                            on_activate_call=self._on_my_saved_party_delete_press,
                            text_scale=tscl,
                            label="Delete",
                            autoselect=True)

            v -= sub_scroll_height + 23
            self._scrollwidget = scrlw = ba.scrollwidget(
                parent=self._container,
                position=(smlh, v),
                size=(sub_scroll_width, sub_scroll_height))
            ba.containerwidget(edit=self._container, selected_child=scrlw)
            self._columnwidget = ba.columnwidget(parent=scrlw,
                                                 left_border=10,
                                                 border=2,
                                                 margin=0)

            
            self._my_saved_party_selected = None
            self._refresh_my_saved_parties()

    def _no_saved_party_selected_error(self) -> None:
        ba.screenmessage(ba.Lstr(resource="No Server Selected"),
                         color=(1, 0, 0))
        ba.playsound(ba.getsound('error'))

    def _on_my_saved_party_press(self) -> None:
        if self._my_saved_party_selected is None:
            self._no_saved_party_selected_error()
            return

        config=ba.app.config['Saved Servers'][self._my_saved_party_selected]
        _ba.connect_to_party(config['addr'],config['port'])

    def _on_my_saved_party_rename_press(self) -> None:
        if self._my_saved_party_selected is None:
            self._no_saved_party_selected_error()
            return
        c_width = 600
        c_height = 250
        uiscale = ba.app.ui.uiscale
        self._my_saved_party_rename_window = cnt = ba.containerwidget(
            scale=(1.8 if uiscale is ba.UIScale.SMALL else
                   1.55 if uiscale is ba.UIScale.MEDIUM else 1.0),
            size=(c_width, c_height),
            transition='in_scale')
        
        ba.textwidget(parent=cnt,
                      size=(0, 0),
                      h_align='center',
                      v_align='center',
                      text="Enter Name of Party",
                      maxwidth=c_width * 0.8,
                      position=(c_width * 0.5, c_height - 60))
        self._my_party_rename_text = txt = ba.textwidget(
            parent=cnt,
            size=(c_width * 0.8, 40),
            h_align='left',
            v_align='center',
            text=ba.app.config['Saved Servers'][self._my_saved_party_selected]['name'],
            editable=True,
            description="Server name text",
            position=(c_width * 0.1, c_height - 140),
            autoselect=True,
            maxwidth=c_width * 0.7,
            max_chars=200)
        cbtn = ba.buttonwidget(
            parent=cnt,
            label=ba.Lstr(resource='cancelText'),
            on_activate_call=ba.Call(
                lambda c: ba.containerwidget(edit=c, transition='out_scale'),
                cnt),
            size=(180, 60),
            position=(30, 30),
            autoselect=True)
        okb = ba.buttonwidget(parent=cnt,
                              label="Rename",
                              size=(180, 60),
                              position=(c_width - 230, 30),
                              on_activate_call=ba.Call(
                                  self._rename_saved_party,
                                  self._my_saved_party_selected),
                              autoselect=True)
        ba.widget(edit=cbtn, right_widget=okb)
        ba.widget(edit=okb, left_widget=cbtn)
        ba.textwidget(edit=txt, on_return_press_call=okb.activate)
        ba.containerwidget(edit=cnt, cancel_button=cbtn, start_button=okb)

    def _rename_saved_party(self, server: str) -> None:
        new_name = None

        
        if not self._my_party_rename_text:
          return
        new_name_raw = cast(
                str, ba.textwidget(query=self._my_party_rename_text))
        ba.app.config['Saved Servers'][server]['name']=new_name_raw
        ba.app.config.commit()
        ba.screenmessage("Renamed Successfully",color=(0,0,1))   
        self._refresh_my_saved_parties()
            

        ba.containerwidget(edit=self._my_saved_party_rename_window,
                           transition='out_scale')

    def _on_my_saved_party_delete_press(self) -> None:
        from bastd.ui import confirm
        if self._my_saved_party_selected is None:
            self._no_saved_party_selected_error()
            return
        confirm.ConfirmWindow(
            "Confirm Delete ?",
            ba.Call(self._delete_saved_party, self._my_saved_party_selected), 450, 150)

    

    def _delete_saved_party(self, server: str) -> None:
        config=ba.app.config['Saved Servers']
        del config[server]
        self._refresh_my_saved_parties()
    def _on_my_saved_party_select(self, server: str) -> None:
        self._my_saved_party_selected = server

    def _refresh_my_saved_parties(self) -> None:
        assert self._columnwidget is not None
        for child in self._columnwidget.get_children():
            child.delete()
        t_scale = 1.6
        
            
        config=ba.app.config
        if 'Saved Servers' in config:
          servers=config['Saved Servers']
        
        else:    
          servers = []

        assert self._my_parties_scroll_width is not None
        assert self._my_saved_party_connect_button is not None
        for server in servers:
            txt = ba.textwidget(
                parent=self._columnwidget,
                size=(self._my_parties_scroll_width / t_scale, 30),
                selectable=True,
                color=(1.0, 1, 0.4) ,
                always_highlight=True,
                on_select_call=ba.Call(self._on_my_saved_party_select, server),
                on_activate_call=self._my_saved_party_connect_button.activate,
                text=config['Saved Servers'][server]['name'] if config['Saved Servers'][server]['name']!='' else config['Saved Servers'][server]['addr']+" "+str(config['Saved Servers'][server]['port']),
                h_align='left',
                v_align='center',
                corner_scale=t_scale,
                maxwidth=(self._my_parties_scroll_width / t_scale) * 0.93)
            
                


    def on_deactivate(self) -> None:
        self._access_check_timer = None

    def _connect(self, textwidget: ba.Widget,
                 port_textwidget: ba.Widget) -> None:
        addr = cast(str, ba.textwidget(query=textwidget))
        if addr == '':
            ba.screenmessage(
                ba.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        try:
            port = int(cast(str, ba.textwidget(query=port_textwidget)))
        except ValueError:
            port = -1
        if port > 65535 or port < 0:
            ba.screenmessage(ba.Lstr(resource='internal.invalidPortErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        _HostLookupThread(name=addr,
                          port=port,
                          call=ba.WeakCall(self._host_lookup_result)).start()

    def _save_server(self, textwidget: ba.Widget,
                 port_textwidget: ba.Widget) -> None:
        addr = cast(str, ba.textwidget(query=textwidget))
        if addr == '':
            ba.screenmessage(
                ba.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        try:
            port = int(cast(str, ba.textwidget(query=port_textwidget)))
        except ValueError:
            port = -1
        if port > 65535 or port < 0:
            ba.screenmessage(ba.Lstr(resource='internal.invalidPortErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        try:
            import socket
            addr = socket.gethostbyname(addr)
        except Exception:
            addr = None
        config=ba.app.config

        if addr is not None:
          if 'Saved Servers' in config:
            config['Saved Servers'][addr+str(port)]={"addr":addr,"port":port,"name":''}
          else:
            config['Saved Servers']={}

            config['Saved Servers'][addr+str(port)]={"addr":addr,"port":port,"name":''}
          config.commit()
          ba.screenmessage("Saved Successfully",
                               color=(0, 1, 0))
        else:
          ba.screenmessage("Invalid Address",
                               color=(1, 0, 0))
    def _host_lookup_result(self, resolved_address: Optional[str],
                            port: int) -> None:
        if resolved_address is None:
            ba.screenmessage(
                ba.Lstr(resource='internal.unableToResolveHostText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
        else:
            # Store for later.
            config = ba.app.config
            config['Last Manual Party Connect Address'] = resolved_address
            config.commit()
            _ba.connect_to_party(resolved_address, port=port)

    def _run_addr_fetch(self) -> None:
        try:
            # FIXME: Update this to work with IPv6.
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            val = sock.getsockname()[0]
            sock.close()
            ba.pushcall(
                ba.Call(
                    _safe_set_text,
                    self._checking_state_text,
                    val,
                ),
                from_other_thread=True,
            )
        except Exception as exc:
            err_str = str(exc)

            # FIXME: Should look at exception types here,
            #  not strings.
            if 'Network is unreachable' in err_str:
                ba.pushcall(ba.Call(
                    _safe_set_text, self._checking_state_text,
                    ba.Lstr(resource='gatherWindow.'
                            'noConnectionText'), False),
                            from_other_thread=True)
            else:
                ba.pushcall(ba.Call(
                    _safe_set_text, self._checking_state_text,
                    ba.Lstr(resource='gatherWindow.'
                            'addressFetchErrorText'), False),
                            from_other_thread=True)
                ba.pushcall(ba.Call(ba.print_error,
                                    'error in AddrFetchThread: ' + str(exc)),
                            from_other_thread=True)

    def _on_show_my_address_button_press(self, v2: float,
                                         container: Optional[ba.Widget],
                                         c_width: float) -> None:
        if not container:
            return

        tscl = 0.85
        tspc = 25

        ba.playsound(ba.getsound('swish'))
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualYourLocalAddressText'))
        self._checking_state_text = ba.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(0.5, 0.5, 0.5),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='left',
            v_align='center',
            text=ba.Lstr(resource='gatherWindow.'
                         'checkingText'))

        threading.Thread(target=self._run_addr_fetch).start()

        v2 -= tspc
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualYourAddressFromInternetText'))

        t_addr = ba.textwidget(parent=container,
                               position=(c_width * 0.5, v2),
                               color=(0.5, 0.5, 0.5),
                               scale=tscl,
                               size=(0, 0),
                               maxwidth=c_width * 0.45,
                               h_align='left',
                               v_align='center',
                               flatness=1.0,
                               text=ba.Lstr(resource='gatherWindow.'
                                            'checkingText'))
        v2 -= tspc
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualJoinableFromInternetText'))

        t_accessible = ba.textwidget(parent=container,
                                     position=(c_width * 0.5, v2),
                                     color=(0.5, 0.5, 0.5),
                                     scale=tscl,
                                     size=(0, 0),
                                     maxwidth=c_width * 0.45,
                                     flatness=1.0,
                                     h_align='left',
                                     v_align='center',
                                     text=ba.Lstr(resource='gatherWindow.'
                                                  'checkingText'))
        v2 -= 28
        t_accessible_extra = ba.textwidget(parent=container,
                                           position=(c_width * 0.5, v2),
                                           color=(1, 0.5, 0.2),
                                           scale=0.7,
                                           size=(0, 0),
                                           maxwidth=c_width * 0.9,
                                           flatness=1.0,
                                           h_align='center',
                                           v_align='center',
                                           text='')

        self._doing_access_check = False
        self._access_check_count = 0  # Cap our refreshes eventually.
        self._access_check_timer = ba.Timer(
            10.0,
            ba.WeakCall(self._access_check_update, t_addr, t_accessible,
                        t_accessible_extra),
            repeat=True,
            timetype=ba.TimeType.REAL)

        # Kick initial off.
        self._access_check_update(t_addr, t_accessible, t_accessible_extra)
        if self._check_button:
            self._check_button.delete()

    def _access_check_update(self, t_addr: ba.Widget, t_accessible: ba.Widget,
                             t_accessible_extra: ba.Widget) -> None:
        from ba.internal import master_server_get

        # If we don't have an outstanding query, start one..
        assert self._doing_access_check is not None
        assert self._access_check_count is not None
        if not self._doing_access_check and self._access_check_count < 100:
            self._doing_access_check = True
            self._access_check_count += 1
            self._t_addr = t_addr
            self._t_accessible = t_accessible
            self._t_accessible_extra = t_accessible_extra
            master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                              callback=ba.WeakCall(
                                  self._on_accessible_response))

    def _on_accessible_response(self, data: Optional[Dict[str, Any]]) -> None:
        t_addr = self._t_addr
        t_accessible = self._t_accessible
        t_accessible_extra = self._t_accessible_extra
        self._doing_access_check = False
        color_bad = (1, 1, 0)
        color_good = (0, 1, 0)
        if data is None or 'address' not in data or 'accessible' not in data:
            if t_addr:
                ba.textwidget(edit=t_addr,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'noConnectionText'),
                              color=color_bad)
            if t_accessible:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'noConnectionText'),
                              color=color_bad)
            if t_accessible_extra:
                ba.textwidget(edit=t_accessible_extra,
                              text='',
                              color=color_bad)
            return
        if t_addr:
            ba.textwidget(edit=t_addr, text=data['address'], color=color_good)
        if t_accessible:
            if data['accessible']:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'manualJoinableYesText'),
                              color=color_good)
                if t_accessible_extra:
                    ba.textwidget(edit=t_accessible_extra,
                                  text='',
                                  color=color_good)
            else:
                ba.textwidget(
                    edit=t_accessible,
                    text=ba.Lstr(resource='gatherWindow.'
                                 'manualJoinableNoWithAsteriskText'),
                    color=color_bad,
                )
                if t_accessible_extra:
                    ba.textwidget(
                        edit=t_accessible_extra,
                        text=ba.Lstr(resource='gatherWindow.'
                                     'manualRouterForwardingText',
                                     subs=[('${PORT}',
                                            str(_ba.get_game_port()))]),
                        color=color_bad,
                    )


def enableeeeee():
    gt.ManualGatherTab=newManualGatherTab
# ba_meta export plugin
class enablee(ba.Plugin):
    
    def __init__(self):
        ba.screenmessage('Server connector by Mr.Smoothy', color=(0, 1, 0))   
        if _ba.env().get("build_number",0) >= 20258:
            enableeeeee()
              
        else:print("only work on 1.5.29 and above ")
    