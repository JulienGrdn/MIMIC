
class Palette:

    # Fonts - Adwaita prefers Cantarell or Inter
    FONT_MAIN = "Cantarell, Inter, Segoe UI, sans-serif"
    FONT_SIZE = "11pt"     # standard body text
    FONT_SIZE_L = "14pt"   # headers
    
    # --- Adwaita Light Theme Palette ---
    L_BG_MAIN       = "#F2F2F2"   # Adwaita Window Background
    L_BG_FRAME_1    = "#FFFFFF"   # Cards / Content Views
    L_BG_FRAME_2    = "#F4F4F4"   # Secondary backgrounds / Headers
    L_TEXT_MAIN     = "#2E3436"   # Adwaita FG
    L_TEXT_SEC      = "#5E5C64"   # Secondary Label
    L_BORDER        = "#DEDEDE"   # Subtle divider
    L_BORDER_FOCUS  = "#3584E4"   # Focus Ring Blue

    # --- Adwaita Dark Theme Palette ---
    D_BG_MAIN       = "#383838"   # Adwaita Dark Window Background
    D_BG_FRAME_1    = "#292929"   # Cards / Content Views (Lighter than BG)
    D_BG_FRAME_2    = "#383838"   # Secondary backgrounds
    D_TEXT_MAIN     = "#efefdf"
    D_TEXT_SEC      = "#d9d9d9"
    D_BORDER        = "#1B1B1B"   # Dark divider
    D_BORDER_FOCUS  = "#3584E4"   # Focus Ring Blue

    # --- Component Colors ---
    # GNOME Blue Accent (Suggested Action)
    ACCENT_BLUE     = "#3584E4"
    ACCENT_BLUE_H   = "#1C71D8"   # Darker blue for hover/press

    # --- Component Colors ---
    # Buttons (Light)
    L_BTN_BG        = "#E9E9E9"
    L_BTN_HOVER     = "#D5D5D5"
    L_BTN_PRESS     = "#B8B8B8"
    
    # Buttons (Dark)
    D_BTN_BG        = "#444444"
    D_BTN_HOVER     = "#555555"
    D_BTN_PRESS     = "#333333"

    # Status & Accents
    ACCENT_BLUE     = "rgb(70, 120, 250)"
    ACCENT_TEAL     = "rgb(90, 200, 170)"
    STATUS_GREEN    = "#4CAF50"   # Start/On
    STATUS_RED      = "#F44336"   # Stop/Off
    STATUS_YELLOW   = "#FFC107"   # Reset
    STATUS_GREY     = "#CCCCCC"   # Disabled/Toggle Off
    
    # Interactions (List Selections)
    D_INT_HOVER     = "#3A3A3A"
    D_INT_SELECT    = "#3584E4"   # Selected is usually Blue in Adwaita
    
    L_INT_HOVER     = "#F6F6F6"
    L_INT_SELECT    = "#3584E4"   # Selected is usually Blue in Adwaita

    # Input Fields
    L_INPUT_BG      = "#FFFFFF"
    D_INPUT_BG      = "#393939"

    
class Style:
    class Default:
        light = f"""
            QWidget {{
                background-color: {Palette.L_BG_MAIN};
                color: {Palette.L_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
            }}
            /* Cards / Frames */
            QFrame {{
                border: none;
                border-radius: 8px;
                background-color: {Palette.L_BG_MAIN};
            }}
            /* Standard Button */
            QPushButton {{
                background-color: {Palette.L_BTN_BG};
                color: {Palette.L_TEXT_MAIN};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Palette.L_BTN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Palette.L_BTN_PRESS};
            }}
            QPushButton:disabled {{
                background-color: #FAFAFA;
                color: #C0C0C0;
                border-color: #E8E8E8;
            }}
            /* Inputs */
            QLineEdit {{
                background-color: {Palette.L_BG_FRAME_2};
                color: {Palette.L_TEXT_SEC};
                padding: 4px;
                border-radius: 6px;
                border: 0px solid {Palette.L_BORDER};
            }}
            QLineEdit:focus {{
                border: 2px solid {Palette.L_BORDER_FOCUS};
                padding: 5px 7px; /* Compensate for 2px border */
            }}
            QLabel {{
                color: {Palette.L_TEXT_MAIN};
            }}
            /* Text Area */
            QPlainTextEdit {{
                background-color: {Palette.L_INPUT_BG};
                color: {Palette.L_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                border: 1px solid {Palette.L_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QPlainTextEdit:focus {{
                border: 2px solid {Palette.L_BORDER_FOCUS};
            }}
            
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}

            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(128, 128, 128, 0.4);
                min-height: 30px;
                border-radius: 4px;
                margin: 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(128, 128, 128, 0.7);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(128, 128, 128, 0.4);
                min-width: 30px;
                border-radius: 4px;
                margin: 1px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(128, 128, 128, 0.7);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        """
        
        dark = f"""
            QWidget {{
                background-color: {Palette.D_BG_MAIN};
                color: {Palette.D_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
            }}
            QFrame {{
                border: none;
                border-radius: 8px;
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {Palette.D_BTN_BG};
                color: {Palette.D_TEXT_MAIN};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Palette.D_BTN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Palette.D_BTN_PRESS};
            }}
            QLineEdit {{
                background-color: {Palette.D_INPUT_BG};
                color: {Palette.D_TEXT_SEC};
                padding: 4px;
                border-radius: 6px;
                border: 0px solid {Palette.D_BORDER};
            }}
            QLineEdit:focus {{
                border: 2px solid {Palette.D_BORDER_FOCUS};
                padding: 5px 7px;
            }}
            QLabel {{
                color: {Palette.D_TEXT_MAIN};
            }}
            QPlainTextEdit {{
                background-color: {Palette.D_INPUT_BG};
                color: {Palette.D_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                border: 1px solid {Palette.D_BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QPlainTextEdit:focus {{
                border: 2px solid {Palette.D_BORDER_FOCUS};
            }}
                        QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}

            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(128, 128, 128, 0.4);
                min-height: 30px;
                border-radius: 4px;
                margin: 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(128, 128, 128, 0.7);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(128, 128, 128, 0.4);
                min-width: 30px;
                border-radius: 4px;
                margin: 1px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(128, 128, 128, 0.7);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        """


    class Frame:
        content_light = f'''
            QFrame {{
                background-color: {Palette.L_BG_FRAME_2};
                border: 0px solid {Palette.L_BORDER};
                border-radius: 8px;
            }}
        '''

        container_light = f'''
            QFrame {{
                background-color: {Palette.L_BG_FRAME_1};
                border: none;
                border-radius: 8px;
            }}
        '''

        content_dark = f'''
            QFrame {{
                background-color: {Palette.D_BG_FRAME_2};
                border: 0px solid {Palette.D_BORDER};
                border-radius: 8px;
            }}
        '''

        container_dark = f'''
            QFrame {{
                background-color: {Palette.D_BG_FRAME_1};
                border: 0px solid {Palette.D_BORDER};
                border-radius: 8px;
            }}
            
            
        '''

    class Button:
        # --- Standard/Neutral Buttons ---
        simple_light = f'''
            QPushButton {{
                background-color: {Palette.L_BTN_BG};
                color: {Palette.L_TEXT_MAIN};
                border-radius: 6px;
                padding: 4px 12px;
                border: 1px solid transparent;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {Palette.L_BTN_HOVER}; }}
            QPushButton:pressed {{ background-color: {Palette.L_BTN_PRESS}; }}
        '''

        white_light = f'''
            QPushButton {{
                background-color: {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                border-radius: 6px;
                padding: 4px 12px;
                border: 1px solid {Palette.L_BORDER};
                font-weight: 500;
            }}
            QPushButton:hover {{ 
                background-color: {Palette.L_BTN_HOVER}; 
                border-color: {Palette.L_BORDER};
            }}
            QPushButton:pressed {{ background-color: {Palette.L_BTN_PRESS}; }}
        '''

        simple_dark = f'''
            QPushButton {{
                background-color: {Palette.D_BTN_BG};
                color: {Palette.D_TEXT_MAIN};
                border-radius: 6px;
                padding: 4px 12px;
                border: 1px solid {Palette.D_BORDER};
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {Palette.D_BTN_HOVER}; }}
            QPushButton:pressed {{ background-color: {Palette.D_BTN_PRESS}; }}
        '''

        start = f'''
            QPushButton {{
                background-color: rgba(76, 175, 80, 0.15);
                color: {Palette.STATUS_GREEN};
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
                font-weight: 650;
            }}
            QPushButton:hover {{ background-color: rgba(76, 175, 80, 0.25); }}
            QPushButton:pressed {{ 
                background-color: {Palette.STATUS_GREEN}; 
                color: #FFFFFF;
            }}
        '''

        stop = f'''
            QPushButton {{
                background-color: rgba(244, 67, 54, 0.15);
                color: {Palette.STATUS_RED};
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
                font-weight: 650;
            }}
            QPushButton:hover {{ background-color: rgba(244, 67, 54, 0.25); }}
            QPushButton:pressed {{ 
                background-color: {Palette.STATUS_RED}; 
                color: #FFFFFF;
            }}
        '''

        reset = f'''
            QPushButton {{
                background-color: rgba(255, 193, 7, 0.15);
                color: {Palette.STATUS_YELLOW}; 
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
                font-weight: 650;
            }}
            QPushButton:hover {{ background-color: rgba(255, 193, 7, 0.25); }}
            QPushButton:pressed {{ 
                background-color: {Palette.STATUS_YELLOW}; 
                color: #FFFFFF;
            }}
        '''

        suggested = f'''
            QPushButton {{
                background-color: rgba(53, 132, 228, 0.15);
                color: #3584E4; 
                border-radius: 6px;
                padding: 4px 8px;
                border: none;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: rgba(53, 132, 228, 0.25); }}
            QPushButton:pressed {{ 
                background-color: #3584E4; 
                color: #FFFFFF;
            }}
        '''

        disabled = f'''
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.05);
                color: {Palette.STATUS_GREY};
                border-radius: 6px;
                padding: 4px 12px;
                border: none;
            }}
        '''

    class Input:
        line_edit_light = f'''
            QLineEdit {{
                background-color: {Palette.L_BG_FRAME_2};
                color: {Palette.L_TEXT_SEC};
                padding: 2px;
                border-radius: 6px;LineEdit
                border: 0px solid {Palette.L_BORDER};
            }}
        '''

        line_edit_light_white = f'''
            QLineEdit {{
                background-color: {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_SEC};
                padding: 2px;
                border-radius: 6px;
                border: 0px solid {Palette.L_BORDER};
            }}
        '''

        line_edit_dark = f'''
            QLineEdit {{
                background-color: #5A5A5A;
                color: {Palette.D_TEXT_SEC};
                padding: 2px;
                border-radius: 6px;
                border: 0px solid {Palette.D_BORDER};
            }}
        '''

        text_edit_light = f'''
            QTextEdit {{
                background-color: {Palette.L_BG_FRAME_2};
                color: {Palette.L_TEXT_SEC};
                padding: 4px;
                border-radius: 6px;
                border: 1px solid {Palette.L_BORDER};
            }}
        '''

        text_edit_dark = f'''
            QTextEdit {{
                background-color: #5A5A5A;
                color: {Palette.D_TEXT_SEC};
                padding: 4px;
                border-radius: 6px;
                border: 1px solid {Palette.D_BORDER};
            }}
        '''

        spinbox_light = f'''
            QSpinBox {{
                background-color: {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                padding: 6px;
                border-radius: 6px;
                border: 1px solid {Palette.L_BORDER};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: transparent;
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {Palette.L_BTN_HOVER};
                border-radius: 3px;
            }}
        '''
        
        spinbox_dark = f'''
            QSpinBox {{
                background-color: {Palette.D_INPUT_BG};
                color: {Palette.D_TEXT_MAIN};
                padding: 6px;
                border-radius: 6px;
                border: 1px solid {Palette.D_BORDER};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: transparent;
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {Palette.D_BTN_HOVER};
                border-radius: 3px;
            }}
        '''
        
        combobox_light = f'''
            QComboBox {{
                background-color: {Palette.L_BTN_BG};
                color: {Palette.L_TEXT_MAIN};
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid {Palette.L_BORDER};
            }}
            QComboBox:hover {{ background-color: {Palette.L_BTN_HOVER}; }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        '''
        combobox_dark = f'''
            QComboBox {{
                background-color: {Palette.D_BTN_BG};
                color: {Palette.D_TEXT_MAIN};
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid {Palette.D_BORDER};
            }}
            QComboBox:hover {{ background-color: {Palette.D_BTN_HOVER}; }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        '''


    class ComboBox:
        light = f"""
            QComboBox {{
                background-color: {Palette.L_BG_FRAME_2};
                color: {Palette.L_TEXT_MAIN};
                font-size: {Palette.FONT_SIZE};
                padding: 2px;
                border-radius: 6px;
                border: 1px solid {Palette.L_BORDER};
            }}

            QComboBox:hover {{
                background-color: {Palette.L_INT_HOVER};
            }}

            QComboBox:focus {{
                border: 2px solid {Palette.L_BORDER_FOCUS};
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 22px;
                border-left: 1px solid {Palette.L_BORDER};
                background: transparent;
            }}

            QComboBox::down-arrow {{
                image: url(src/mimic/assets/dropdownlight.svg);
                width: 12px;
                height: 12px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {Palette.L_BG_FRAME_1};
                border: 1px solid {Palette.L_BORDER};
                border-radius: 6px;
                padding: 4px;
                outline: 0;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: {Palette.L_INT_HOVER};
            }}

            QComboBox QAbstractItemView::item:selected {{
                background-color: {Palette.L_INT_SELECT};
                color: white;
            }}
            QComboBox QAbstractItemView::viewport {{
                background-color: {Palette.L_BG_FRAME_2};
                border-radius: 6px; /* Match the parent radius */
            }}
        """

        dark = f"""
            QComboBox {{
                background-color: {Palette.D_INPUT_BG};
                color: {Palette.D_TEXT_MAIN};
                font-size: {Palette.FONT_SIZE};
                padding: 1px;
                border-radius: 6px;
                border: 1px solid {Palette.D_BORDER};
            }}

            QComboBox:hover {{
                background-color: {Palette.D_INT_HOVER};
            }}

            QComboBox:focus {{
                border: 2px solid {Palette.D_BORDER_FOCUS};
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 22px;
                border-left: 1px solid {Palette.D_BORDER};
                background: transparent;
            }}

            QComboBox::down-arrow {{
                image: url(src/mimic/assets/dropdowndark.svg);
                width: 12px;
                height: 12px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {Palette.D_BG_FRAME_1};
                border: 1px solid {Palette.D_BORDER};
                border-radius: 6px;
                padding: 1px;
                outline: 0;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: {Palette.D_INT_HOVER};
            }}

            QComboBox QAbstractItemView::item:selected {{
                background-color: {Palette.D_INT_SELECT};
                color: white;
            }}
            QComboBox QAbstractItemView::viewport {{
                background-color: {Palette.D_BG_FRAME_1};
                border-radius: 6px; /* Match the parent radius */
            }}
        """

    class Slider:
        standard_light = f'''
            QSlider::groove:horizontal {{
                border: 0px;
                height: 4px;
                background: #DEDEDE;
                margin: 2px 0;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {Palette.L_BG_FRAME_1};
                border: 1px solid #DEDEDE;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
                width: 20px;
                height: 20px;
                margin: -8px 0; 
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #F6F6F6;
                border: 1px solid #C0C0C0;
            }}
            QSlider::sub-page:horizontal {{
                background: {Palette.ACCENT_BLUE};
                height: 4px;
                border-radius: 2px;
            }}
        '''

        standard_dark = f'''
            QSlider::groove:horizontal {{
                border: 0px;
                height: 4px;
                background: #454545;
                margin: 2px 0;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #D0D0D0;
                border: none;
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #FFFFFF;
            }}
            QSlider::sub-page:horizontal {{
                background: {Palette.ACCENT_BLUE};
                height: 4px;
                border-radius: 2px;
            }}
        '''

        toggle_switch = f'''
            QCheckBox::indicator {{
                width: 44px;
                height: 24px;
                border-radius: 12px;
                background-color: #E0E0E0;
                border: 1px solid transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Palette.ACCENT_BLUE};
                border: 1px solid {Palette.ACCENT_BLUE};
            }}
            QCheckBox::indicator:hover {{
                background-color: #D6D6D6;
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {Palette.ACCENT_BLUE_H};
            }}
            QCheckBox::indicator:before {{
                content: '';
                position: absolute;
                width: 20px;
                height: 20px;
                background-color: #FFFFFF;
                border-radius: 10px;
                top: 2px;
                left: 2px;
            }}
            /* Note: QSS does not support 'transition'. 
               Animation requires QPropertyAnimation in Python code. 
               This visualizes the end state. */
            QCheckBox::indicator:checked:before {{
                left: 22px;
            }}
        '''

    class Label:
        title_light = f'''
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Palette.L_TEXT_MAIN};
                padding: 4px;
            }}
        '''
        
        title_dark = f'''
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Palette.D_TEXT_MAIN};
                padding: 4px;
            }}
        '''

        live_value_big_light = f'''
            QLabel {{
                font-size: 20px;
                font-weight: 500; /* Light weight for large text */
                color: {Palette.L_TEXT_MAIN};
                padding: 5px;
            }}
        '''

        live_value_big_dark = f'''
            QLabel {{
                font-size: 20px;
                font-weight: 300; /* Light weight for large text */
                color: {Palette.D_TEXT_MAIN};
                padding: 5px;
            }}
        '''

        frequency_big = f'''
            QLabel {{
                font-size: 26px;
                font-weight: 300; /* Light weight for large text */
                color: {Palette.L_TEXT_MAIN};
                padding: 5px;
            }}
        '''

        frequency_big_dark = f'''
            QLabel {{
                font-size: 26px;
                font-weight: 300; /* Light weight for large text */
                color: {Palette.D_TEXT_MAIN};
                padding: 5px;
            }}
        '''
        
        frequency_big_stable = f'''
            QLabel {{
                font-size: 26px;
                font-weight: 300;
                color: {Palette.STATUS_GREEN};
                padding: 5px;
            }}
        '''

        parameter = f'''
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {Palette.L_TEXT_SEC};
                padding: 4px;
            }}
        '''

        parameter_dark = f'''
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {Palette.D_TEXT_SEC};
                padding: 4px;
            }}
        '''

    class Scroll:
        combined = """
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.4);
                min-height: 30px;
                border-radius: 4px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(128, 128, 128, 0.4);
                min-width: 30px;
                border-radius: 4px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(128, 128, 128, 0.7);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """
        
        transparent = """
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.4);
                min-height: 30px;
                border-radius: 4px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(128, 128, 128, 0.4);
                min-width: 30px;
                border-radius: 4px;
                margin: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(128, 128, 128, 0.7);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """

    class List:
        dark = f"""
            QListWidget {{
                background-color:  {Palette.D_BG_FRAME_1};
                color: {Palette.D_TEXT_MAIN};
                border: none;
                font-size: {Palette.FONT_SIZE};
                outline: none;
                border-radius: 0px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 4px;
                margin: 2px 4px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {Palette.ACCENT_BLUE};
                color: #FFFFFF;
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(255, 255, 255, 0.07);
            }}
        """

        light = f"""
            QListWidget {{
                background-color:  {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                border: none;
                font-size: {Palette.FONT_SIZE};
                outline: none;
                border-radius: 0px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 4px;
                margin: 2px 4px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {Palette.ACCENT_BLUE};
                color: #FFFFFF;
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(0, 0, 0, 0.05);
            }}
        """

        secondary_light = f"""
            QListWidget {{
                background-color: {Palette.L_BG_FRAME_2};
                color: {Palette.L_TEXT_MAIN};
                border-right: 0px solid {Palette.L_BORDER};
                border-radius: 0px;
                padding: 6px;
                font-size: {Palette.FONT_SIZE};
                outline: none;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 10px;
                margin: 2px 0px; 
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: #E6E6E6; /* Adwaita Sidebar Selection is often Grey, not Blue */
                color: {Palette.L_TEXT_MAIN};
            }}
            QListWidget::item:hover {{
                background-color: rgba(0,0,0,0.04);
            }}
        """
        
  
    class GroupBox:
        light = f"""
            QGroupBox {{
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                background-color: {Palette.L_BG_FRAME_1};
                font-family: '{Palette.FONT_MAIN}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 1px;
                padding: 4px 8px;
                color: {Palette.L_TEXT_MAIN};
                font-weight: bold;
                font-size: {Palette.FONT_SIZE};
                background-color: transparent;
            }}
            QLabel {{
                background-color: {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
                padding: 2px;
            }}
        """

        light_nolabel = f"""
            QGroupBox {{
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                background-color: {Palette.L_BG_FRAME_1};
                font-family: '{Palette.FONT_MAIN}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 1px;
                padding: 4px 8px;
                color: {Palette.L_TEXT_MAIN};
                font-weight: bold;
                font-size: {Palette.FONT_SIZE};
                background-color: transparent;
            }}
        """

        light_gray = f"""
            QGroupBox {{
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                background-color: {Palette.L_BG_FRAME_2};
                font-family: '{Palette.FONT_MAIN}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 1px;
                padding: 4px 8px;
                color: {Palette.L_TEXT_MAIN};
                font-weight: bold;
                font-size: {Palette.FONT_SIZE};
                background-color: transparent;
            }}
            QLabel {{
                background-color: {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
                padding: 2px;
            }}
        """

        dark = f"""
            QGroupBox {{
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                background-color: {Palette.D_BG_FRAME_1};
                font-family: '{Palette.FONT_MAIN}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 4px;
                color: {Palette.D_TEXT_MAIN};
                font-weight: bold;
                font-size: {Palette.FONT_SIZE};
            }}

            QLabel {{
                background-color: {Palette.D_BG_FRAME_1};
                color: #ffffff;         /* force white text */
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
                padding: 2px;
            }}
        """

        dark_gray = f"""
            QGroupBox {{
                border: 0px solid {Palette.D_BORDER};
                border-radius: 8px;
                margin-top: 24px;
                background-color: {Palette.D_BG_FRAME_2};
                font-family: '{Palette.FONT_MAIN}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 4px;
                color: {Palette.D_TEXT_MAIN};
                font-weight: bold;
                font-size: {Palette.FONT_SIZE};
            }}
            QLabel {{
                background-color: {Palette.D_BG_FRAME_2};
                color: #ffffff;         /* force white text */
                font-family: '{Palette.FONT_MAIN}';
                font-size: {Palette.FONT_SIZE};
                padding: 2px;
            }}
        """


    class AnimatedListBar:
        container_light = f"""
            QWidget {{
                background-color: {Palette.L_BG_FRAME_1};
                border: none;
            }}
        """

        container_dark = f"""
            QWidget {{
                background-color: {Palette.D_BG_FRAME_1};
                border: none;
            }}
        """
        list_light = f"""
            QListWidget {{
                background-color:  {Palette.L_BG_FRAME_1};
                color: {Palette.L_TEXT_MAIN};
                border: none;
                font-size: {Palette.FONT_SIZE};
                outline: none;
                border-radius: 0px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 4px;
                margin: 2px 4px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {Palette.ACCENT_BLUE};
                color: #FFFFFF;
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(255, 255, 255, 0.07);
            }}
        """
        list_dark = f"""
            QListWidget {{
                background-color:  {Palette.D_BG_FRAME_1};
                color: {Palette.D_TEXT_MAIN};
                border: none;
                font-size: {Palette.FONT_SIZE};
                outline: none;
                border-radius: 0px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 4px;
                margin: 2px 4px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {Palette.ACCENT_BLUE};
                color: #FFFFFF;
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(255, 255, 255, 0.07);
            }}
        """
        toggle_light = f"""
            QPushButton {{
                background-color: {Palette.L_BG_FRAME_1};
                border: none;
                border-radius: 0px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.06);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.12);
            }}
        """
        toggle_dark = f"""
            QPushButton {{
                background-color: {Palette.D_BG_FRAME_1};
                border: none;
                border-radius: 0px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.07);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.13);
            }}
        """


from typing import Union, Optional

class HTMLValueFormatter:
    Style = Palette
    def __init__(self, sig_digits: int = 10,  unit: Optional[str] = None):
        self.sig_digits = sig_digits
        self.main_color = self.Style.L_TEXT_MAIN
        self.unit_color = "#888888"
        self.unit = unit

    def set_theme(self, is_dark: bool):
        if is_dark:
            self.main_color = self.Style.D_TEXT_MAIN
        else:
            self.main_color = self.Style.L_TEXT_MAIN

    def get_html(self, value: Union[int, float]) -> str:
        if value is None:
            return ""

        if isinstance(value, int):
            val_str = f"{value}"
        else:
            val_str = f"{value:.{self.sig_digits}g}"

        html = f"<span style='font-size: 22px; font-weight: 500; color: {self.main_color};'>{val_str}</span>"

        if self.unit:
            html += f" <span style='font-size: 12px; font-weight: 300; color: {self.unit_color};'>{self.unit}</span>"

        return html