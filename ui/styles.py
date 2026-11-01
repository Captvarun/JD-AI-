"""
QSS Stylesheets and visual theme for JD Desktop Assistant.
Palette inspired by the JD robotic helmet (dark charcoal, glowing mint eyes, lilac tints).
"""

from core.config import (
    COLOR_BG_DARK,
    COLOR_CARD_DARK,
    COLOR_HEADER_DARK,
    COLOR_BORDER,
    COLOR_BORDER_FOCUS,
    COLOR_MINT,
    COLOR_MINT_HOVER,
    COLOR_MINT_BG,
    COLOR_LILAC,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)

MAIN_STYLESHEET = f"""
/* Root Container */
#MainCard {{
    background-color: {COLOR_BG_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: 18px;
}}

/* Top Header Bar */
#HeaderWidget {{
    background-color: {COLOR_HEADER_DARK};
    border-top-left-radius: 17px;
    border-top-right-radius: 17px;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 8px 12px;
}}

#TitleLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

#SubtitleLabel {{
    color: {COLOR_LILAC};
    font-size: 11px;
}}

#BadgeOnline {{
    background-color: {COLOR_MINT_BG};
    color: {COLOR_MINT};
    border: 1px solid {COLOR_MINT};
    border-radius: 9px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 0.8px;
}}

#ShortcutBadge {{
    background-color: #1A1F2B;
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid #2B3345;
    border-radius: 5px;
    padding: 2px 6px;
    font-size: 10px;
    font-family: Consolas, monospace;
}}

/* Window Control Buttons */
.WindowCtrlBtn {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    width: 26px;
    height: 26px;
}}

.WindowCtrlBtn:hover {{
    background-color: #262D3D;
    color: {COLOR_TEXT_PRIMARY};
}}

#BtnClose:hover {{
    background-color: #E03E3E;
    color: white;
}}

/* Chat Scroll Area */
#ChatScrollArea {{
    background-color: transparent;
    border: none;
}}

#ChatContentWidget {{
    background-color: transparent;
}}

/* Custom ScrollBar */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 4px 0 4px 0;
}}

QScrollBar::handle:vertical {{
    background: #2A3142;
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_MINT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Input Area Container */
#InputAreaContainer {{
    background-color: {COLOR_CARD_DARK};
    border-top: 1px solid {COLOR_BORDER};
    border-bottom-left-radius: 17px;
    border-bottom-right-radius: 17px;
    padding: 10px 12px;
}}

/* Text Input Field */
#MessageInput {{
    background-color: #0E1015;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {COLOR_MINT};
    selection-color: #000000;
}}

#MessageInput:focus {{
    border: 1px solid {COLOR_BORDER_FOCUS};
    background-color: #12151D;
}}

/* Action Buttons (Send, Mic, TTS) */
#BtnSend {{
    background-color: {COLOR_MINT};
    color: #0A110D;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 14px;
}}

#BtnSend:hover {{
    background-color: {COLOR_MINT_HOVER};
}}

#BtnSend:pressed {{
    background-color: #38E5A0;
}}

#BtnMic {{
    background-color: #1E2431;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    font-size: 14px;
    padding: 8px 10px;
}}

#BtnMic:hover {{
    border: 1px solid {COLOR_MINT};
    color: {COLOR_MINT};
}}

#BtnMic[active="true"] {{
    background-color: {COLOR_MINT_BG};
    border: 1px solid {COLOR_MINT};
    color: {COLOR_MINT};
}}

#BtnTTS {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    border-radius: 6px;
    font-size: 13px;
    padding: 4px;
}}

#BtnTTS:hover {{
    color: {COLOR_TEXT_PRIMARY};
    background-color: #202634;
}}
"""
