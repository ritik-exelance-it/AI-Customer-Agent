"""Dark, high-contrast visual styling for the Streamlit support workspace."""
import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            --page: #0B1120;
            --surface: #111B2E;
            --surface-raised: #17243A;
            --surface-input: #0D1728;
            --text: #E8EEF8;
            --muted: #A7B5CA;
            --primary: #7CB7FF;
            --primary-hover: #A3CDFF;
            --border: #2A3A54;
            --success: #34D399;
            --warning: #FBBF24;
            --error: #FB7185;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: var(--page) !important;
            color: var(--text) !important;
        }
        [data-testid="stHeader"] {
            background-color: rgba(11, 17, 32, .94) !important;
        }
        [data-testid="stAppViewContainer"] .main .block-container {
            max-width: 1500px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        .stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stWidgetLabel"],
        .stApp [data-testid="stMarkdownContainer"] span {
            color: var(--text) !important;
        }
        .stApp a { color: var(--primary) !important; }
        .stApp a:hover { color: var(--primary-hover) !important; }
        .stApp [data-testid="stCaptionContainer"] p,
        .stApp small { color: var(--muted) !important; }

        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: var(--text) !important;
        }
        .sidebar-brand {
            color: var(--text);
            font-size: 1.4rem;
            font-weight: 800;
            letter-spacing: -.03em;
        }

        .brand-kicker, .welcome-eyebrow, .prompt-label {
            color: var(--primary);
            letter-spacing: .12em;
            font-size: .68rem;
            font-weight: 750;
        }
        .page-title {
            color: var(--text) !important;
            font-size: 2rem;
            line-height: 1.15;
            font-weight: 750;
            margin: .25rem 0;
        }
        .page-subtitle, .welcome-copy {
            color: var(--muted) !important;
            line-height: 1.65;
            font-size: .95rem;
        }
        .status-label {
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            border: 1px solid var(--border);
            background: var(--surface);
            border-radius: 999px;
            padding: .55rem .8rem;
            color: var(--text);
            font-size: .82rem;
            margin-top: 1.25rem;
        }
        .status-dot, .agent-status-dot {
            width: 8px;
            height: 8px;
            display: inline-block;
            flex: 0 0 8px;
            border-radius: 50%;
            background: var(--success);
        }
        .welcome-title {
            color: var(--text) !important;
            font-size: 1.8rem;
            line-height: 1.2;
            margin: .45rem 0 .6rem;
        }
        .prompt-label { margin: 1.1rem 0 .4rem; }
        .context-heading {
            color: var(--text) !important;
            font-size: 1.08rem;
            font-weight: 750;
            margin: .25rem 0 1rem;
        }
        .panel-title {
            color: var(--text) !important;
            font-weight: 700;
            font-size: .93rem;
            margin-bottom: .35rem;
        }
        .footer-note {
            color: var(--muted) !important;
            font-size: .78rem;
            border-top: 1px solid var(--border);
            padding-top: .8rem;
            margin-top: 1.5rem;
        }

        .agent-status {
            display: flex;
            align-items: flex-start;
            gap: .7rem;
            padding: .85rem;
            margin: .35rem 0 .65rem;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
        }
        .agent-status-dot { margin-top: .36rem; }
        .agent-status--working .agent-status-dot {
            background: var(--primary);
            box-shadow: 0 0 0 4px rgba(124, 183, 255, .16);
            animation: agent-pulse 1.5s ease-in-out infinite;
        }
        .agent-status--completed .agent-status-dot { background: var(--success); }
        .agent-status--failed .agent-status-dot { background: var(--error); }
        .agent-status--ready .agent-status-dot { background: var(--muted); }
        .agent-status-copy { display: flex; flex-direction: column; gap: .2rem; }
        .agent-status-copy strong { color: var(--text); font-size: .9rem; }
        .agent-status-copy small { color: var(--muted); line-height: 1.45; }
        .activity-entry {
            color: var(--muted);
            font-size: .82rem;
            line-height: 1.5;
            border-left: 1px solid var(--border);
            margin: .25rem 0 .25rem .23rem;
            padding: .25rem 0 .25rem .8rem;
        }
        .activity-entry span { color: var(--muted); }
        .activity-entry strong { color: var(--text); }
        .activity-log {
            border-left: 1px solid var(--border);
            margin: .3rem 0 .4rem .23rem;
            padding-left: .8rem;
        }
        .activity-log p {
            color: var(--muted) !important;
            font-size: .82rem;
            line-height: 1.5;
            margin: .4rem 0;
        }
        .activity-log strong { color: var(--text) !important; }
        @keyframes agent-pulse {
            50% { box-shadow: 0 0 0 7px rgba(124, 183, 255, .06); }
        }

        [data-testid="stChatMessage"] {
            background: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: .85rem 1rem;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stChatMessage"] li {
            color: var(--text) !important;
        }
        [data-testid="stChatInput"] {
            background: var(--surface-input) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
        }
        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted) !important;
            -webkit-text-fill-color: var(--muted) !important;
            opacity: 1;
        }
        input, textarea, [data-baseweb="select"] > div {
            background-color: var(--surface-input) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }
        input::placeholder, textarea::placeholder {
            color: var(--muted) !important;
            opacity: 1;
        }

        div.stButton > button, [data-testid="stDownloadButton"] button {
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--surface-raised);
            color: var(--text);
            min-height: 2.65rem;
            text-align: left;
        }
        div.stButton > button:hover, [data-testid="stDownloadButton"] button:hover {
            border-color: var(--primary);
            color: var(--primary-hover);
            background: #1B2B44;
        }
        div.stButton > button[kind="primary"] {
            background: #1D4ED8;
            border-color: #3B82F6;
            color: #FFFFFF;
        }
        div.stButton > button:disabled,
        [data-testid="stDownloadButton"] button:disabled {
            color: #8795A9 !important;
            background: #172033 !important;
            border-color: #2A3548 !important;
        }
        [data-testid="stRadio"] label { color: var(--text) !important; }
        [data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
        }
        [data-testid="stStatusWidget"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
        }
        [data-testid="stAlert"] { color: var(--text) !important; }
        hr { border-color: var(--border); }
        :focus-visible { outline: 2px solid var(--primary) !important; outline-offset: 2px; }

        @media (max-width: 850px) {
            .page-title { font-size: 1.6rem; }
            .welcome-title { font-size: 1.4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
