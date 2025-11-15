import streamlit as st
import json
import os
from datetime import datetime
from streamlit.runtime.scriptrunner import get_script_run_ctx

# --- Constants and Setup ---

CHAT_HISTORY_FILE = "chats.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---

def load_conversations():
    """Loads conversations and migrates any old data structures."""
    migrated = False
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            try:
                data = json.load(f)
                # Migration logic
                for chat_name, content in data.items():
                    if isinstance(content, list):
                        data[chat_name] = {
                            "created_at": datetime.now().isoformat(),
                            "messages": content
                        }
                        migrated = True
                
                # Ensure at least one chat exists if data was loaded but empty
                if not data:
                    data = {"Chat 1": {"created_at": datetime.now().isoformat(), "messages": []}}
                    migrated = True

                if migrated:
                    save_conversations(data)
                return data
            except (json.JSONDecodeError, AttributeError, EOFError):
                # Handle empty or corrupted JSON file
                pass
    
    # Return default initial state
    return {"Chat 1": {"created_at": datetime.now().isoformat(), "messages": []}}

def save_conversations(conversations):
    """Safely saves the conversation history using a temporary file."""
    tmp_file = CHAT_HISTORY_FILE + ".tmp"
    with open(tmp_file, "w") as f:
        json.dump(conversations, f, indent=4)
    # Use os.replace for atomic file replacement
    os.replace(tmp_file, CHAT_HISTORY_FILE)

def get_session_id():
    """Gets the unique session ID for the current user."""
    ctx = get_script_run_ctx()
    if ctx is None:
        # Fallback for non-Streamlit environment (should not happen in a running app)
        return "non_streamlit_session"
    return ctx.session_id

# --- Page and Session State Setup ---

st.set_page_config(page_title="CodeGenie", page_icon="💬", layout="wide")

# Initialize session state variables
if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()
if "current_chat" not in st.session_state:
    # Ensure current_chat is set to the first available chat name
    if not st.session_state.conversations:
        st.session_state.conversations = {"Chat 1": {"created_at": datetime.now().isoformat(), "messages": []}}
    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
if "show_share_dialog_for" not in st.session_state:
    st.session_state.show_share_dialog_for = None
if "show_rename_dialog_for" not in st.session_state:
    st.session_state.show_rename_dialog_for = None
if "chat_input_key" not in st.session_state:
    # Key to clear chat input after submission
    st.session_state.chat_input_key = 0

# --- Sidebar ---

with st.sidebar:
    st.image("logo.png", width=80)
    st.title("💬 CodeGenie")
    st.caption("Your AI Coding Assistant")
    st.divider()

    # Create new chat
    if st.button("➕ New Chat", key="new_chat_button", use_container_width=True):
        i = 1
        # Find a unique name for the new chat
        while True:
            new_chat_name = f"Chat {len(st.session_state.conversations) + i}"
            if new_chat_name not in st.session_state.conversations:
                break
            i += 1
            
        st.session_state.conversations[new_chat_name] = {"created_at": datetime.now().isoformat(), "messages": []}
        st.session_state.current_chat = new_chat_name
        save_conversations(st.session_state.conversations)
        st.rerun()

    # Chat list
    st.subheader("Chats")
    
    # Sort chats by creation time (most recent first)
    sorted_chats = sorted(
        st.session_state.conversations.items(),
        key=lambda item: item[1].get("created_at", datetime.min.isoformat()),
        reverse=True
    )

    for chat_name, _ in sorted_chats:
        col1, col2 = st.columns([0.8, 0.2])
        
        # Use a unique key for the button based on the chat name
        select_key = f"select_{chat_name}"
        
        with col1:
            button_type = "primary" if chat_name == st.session_state.current_chat else "secondary"
            if st.button(chat_name, key=select_key, use_container_width=True, type=button_type):
                st.session_state.current_chat = chat_name
                st.rerun()
                
        with col2:
            # Popover for options
            with st.popover("...", use_container_width=True):
                # Rename Dialog
                if st.button(f"✏️ Rename", key=f"rename_dialog_{chat_name}"):
                    st.session_state.show_rename_dialog_for = chat_name
                    st.rerun()
                
                # Share Dialog (Placeholder)
                if st.button(f"🔗 Share", key=f"share_dialog_{chat_name}"):
                    st.session_state.show_share_dialog_for = chat_name
                    st.rerun()
                    
                # Delete Chat
                if st.button(f"🗑️ Delete", key=f"delete_chat_{chat_name}", type="primary"):
                    if len(st.session_state.conversations) > 1:
                        del st.session_state.conversations[chat_name]
                        # Set current chat to the first one remaining
                        st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
                        save_conversations(st.session_state.conversations)
                        st.rerun()
                    else:
                        st.toast("⚠️ Cannot delete the last chat.")

# --- Rename Dialog Logic ---
if st.session_state.show_rename_dialog_for:
    chat_to_rename = st.session_state.show_rename_dialog_for
    with st.form(key=f"rename_form_{chat_to_rename}"):
        new_name = st.text_input("New Chat Name", value=chat_to_rename)
        col_ok, col_cancel = st.columns([1, 1])
        with col_ok:
            submit_button = st.form_submit_button("Rename", type="primary")
        with col_cancel:
            cancel_button = st.form_submit_button("Cancel")
            
    if submit_button:
        if new_name and new_name != chat_to_rename:
            if new_name in st.session_state.conversations:
                st.error("A chat with this name already exists.")
            else:
                # Perform the rename
                old_data = st.session_state.conversations.pop(chat_to_rename)
                st.session_state.conversations[new_name] = old_data
                if st.session_state.current_chat == chat_to_rename:
                    st.session_state.current_chat = new_name
                save_conversations(st.session_state.conversations)
                st.session_state.show_rename_dialog_for = None
                st.rerun()
        elif new_name == chat_to_rename:
            st.warning("New name is the same as the old name.")
            st.session_state.show_rename_dialog_for = None
            st.rerun()
        else:
            st.error("Chat name cannot be empty.")
            
    if cancel_button:
        st.session_state.show_rename_dialog_for = None
        st.rerun()

# --- Main Chat Area ---

st.title(f"🤖 {st.session_state.current_chat}")
# Ensure the current chat exists before trying to access it
current_chat_data = st.session_state.conversations.get(st.session_state.current_chat)

if current_chat_data:
    # Display existing chat messages
    for message in current_chat_data["messages"]:
        # Use a try-except block to safely handle missing 'role' or malformed messages
        try:
            role = message["role"]
            with st.chat_message(role):
                msg_type = message.get("type", "text")
                
                # Path should be relative to the user's session to prevent path traversal issues
                # For this simple app, we'll keep it simple, but in a real app, file_path should be secured.
                file_path = message.get("file_path")
                
                if msg_type == "text":
                    st.markdown(message["content"])
                elif msg_type == "image" and file_path:
                    # Use a unique key for the image to prevent Streamlit warnings
                    st.image(file_path, caption=message.get("content", "Image"), use_column_width=True)
                elif msg_type == "audio" and file_path:
                    st.audio(file_path)
                elif msg_type == "file" and file_path:
                    # Use os.path.basename for security and clean display
                    display_name = os.path.basename(message.get("content", os.path.basename(file_path)))
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                            st.download_button(
                                label=f"📎 Download {display_name}",
                                data=file_bytes,
                                file_name=display_name,
                                key=f"download_{file_path}" # Unique key for download button
                            )
                    except FileNotFoundError:
                        st.error(f"File not found: {display_name}")
                else:
                    st.warning(f"Unsupported message type or missing file_path: {msg_type}")
        except KeyError:
            st.error("Malformed message found in conversation history.")

    # --- Chat Input & File Upload (Main Bar) ---
    
    # Use a unique, session-scoped upload directory to prevent file name collisions
    session_upload_dir = os.path.join(UPLOAD_DIR, get_session_id())
    os.makedirs(session_upload_dir, exist_ok=True)
    
    # Reverting to the original input structure, which is the standard way to handle st.chat_input
    # and st.file_uploader in a chat application.
    
    # st.chat_input is a special component that cannot be placed in a column.
    prompt = st.chat_input("Ask CodeGenie anything...")
    
    # File Uploader is now discreetly placed in a popover, triggered by a plus button.
    with st.popover("➕", help="Attach files (images, audio, or documents)."):
        uploaded_files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            label_visibility="visible"
        )

    # --- Handle Chat and File Uploads ---
    
    # The logic for st.chat_input and st.file_uploader must be outside a form.
    # st.chat_input returns the prompt when submitted, and is None otherwise.
    # st.file_uploader returns the list of files when a file is uploaded, and is empty otherwise.
    
    if prompt or uploaded_files:
        # Text message
        if prompt:
            current_chat_data["messages"].append({"role": "user", "content": prompt, "type": "text"})
            # Placeholder for actual AI response logic
            from llm import get_gemini_response
            response = get_gemini_response(prompt)

            current_chat_data["messages"].append({"role": "assistant", "content": response, "type": "text"})
        
        # File uploads
        if uploaded_files:
            for file in uploaded_files:
                # Save file to the session-specific directory
                file_path = os.path.join(session_upload_dir, file.name)
                
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
        
                file_type = "file"
                if file.type and file.type.startswith("image/"):
                    file_type = "image"
                elif file.type and file.type.startswith("audio/"):
                    file_type = "audio"
        
                # User message for file upload
                current_chat_data["messages"].append({
                    "role": "user",
                    "type": file_type,
                    "file_path": file_path,
                    "content": file.name # content is the display name
                })
                
                # Assistant response for file upload
                response = f"Received your {file_type}: **{file.name}**"
                current_chat_data["messages"].append({"role": "assistant", "content": response, "type": "text"})
        
        # Save and rerun to update the chat display
        save_conversations(st.session_state.conversations)
        st.rerun()
