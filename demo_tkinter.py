import tkinter as tk
from tkmacosx import Button
import time
import threading
import queue
from pynput import keyboard
from smol_tools.summarizer import SmolSummarizer
from smol_tools.rewriter import SmolRewriter
from pynput.keyboard import Key, Controller
import pyperclip
from smol_tools.agent import SmolToolAgent
from smol_tools.chatter import SmolChatter
from smol_tools.titler import SmolTitler
import os
import getpass

class TextPopupApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Start with the window hidden
        self.last_text = ""
        self.active_popups = []
        self.last_summary = ""
        
        # Initialize tools
        self.summarizer = SmolSummarizer()
        self.rewriter = SmolRewriter()
        self.titler = SmolTitler()
        self.agent = SmolToolAgent()
        self.chatter = SmolChatter()
        
        self.keyboard_controller = Controller()
        
        # Replace the keyboard listener with GlobalHotKeys
        self.keyboard_listener = keyboard.GlobalHotKeys({
            "<F8>": self.show_chat_window,
            "<F9>": self.on_f9,
            "<F10>": self.on_f10,
            "<ctrl>+s": self.on_f10 
        })
        self.keyboard_listener.start()
        
        self.username = getpass.getuser()  # Get system username

    def on_f9(self):
        selected_text = self.get_selected_text()
        if selected_text:
            # Directly generate summary instead of showing confirmation popup
            self.generate_summary_direct(selected_text)

    # New method to directly show summary window
    def generate_summary_direct(self, text):
        summary_popup = tk.Toplevel(self.root)
        summary_popup.withdraw()  # Hide the window initially
        self.active_popups.append(summary_popup)
        summary_popup.title("Summary")
        summary_popup.configure(bg='#f6f8fa')  # Very light blue-gray background
        
        # Original text section
        original_frame = tk.Frame(
            summary_popup, 
            bg='white',  # Pure white background
            highlightbackground='#e1e4e8',  # Subtle border color
            highlightthickness=1,
            bd=0,
            relief=tk.FLAT
        )
        original_frame.pack(padx=20, pady=(20,10), fill=tk.X)
        
        # Add original text preview with modern styling
        original_label = tk.Label(
            original_frame, 
            text="Original text", 
            wraplength=300, 
            justify=tk.LEFT,
            bg='white',
            fg='#24292e',  # Dark gray, almost black
            font=('Segoe UI', 12)
        )
        original_label.pack(padx=15, pady=(12,0), anchor='w')
        
        preview = text[:100] + "..." if len(text) > 100 else text
        preview_label = tk.Label(
            original_frame, 
            text=preview, 
            wraplength=300, 
            justify=tk.LEFT,
            bg='white',
            fg='#586069'  # Medium gray for content
        )
        preview_label.pack(padx=15, pady=(5,12), anchor='w')
        
        # Summary section
        summary_frame = tk.Frame(
            summary_popup, 
            bg='white',
            highlightbackground='#e1e4e8',
            highlightthickness=1,
            bd=0,
            relief=tk.FLAT
        )
        summary_frame.pack(padx=20, pady=(10,20), fill=tk.X)
        
        # Create summary label with matching styling
        summary_title = tk.Label(
            summary_frame, 
            text="Summary", 
            wraplength=300, 
            justify=tk.LEFT,
            bg='white',
            fg='#24292e',
            font=('Segoe UI', 12)
        )
        summary_title.pack(padx=15, pady=(12,0), anchor='w')
        
        summary_label = tk.Label(
            summary_frame, 
            text="Generating summary...", 
            wraplength=300, 
            justify=tk.LEFT,
            bg='white',
            fg='#586069'
        )
        summary_label.pack(padx=15, pady=(5,12), anchor='w')
        
        # Add button frame right away
        button_frame = tk.Frame(summary_popup, bg='#f6f8fa')
        button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # Add styled "Draft Reply?" button using tkmacosx
        draft_btn = Button(
            button_frame, 
            text="✏️   Draft Reply",
            command=lambda: [
                self.show_draft_input(summary_popup.winfo_x(), summary_popup.winfo_y(), summary_popup.winfo_width()),
                summary_popup.destroy()
            ],
            font=('Segoe UI', 14),
            bg='#0066FF',
            fg='white',
            activebackground='#0052CC',
            activeforeground='white',
            borderless=True,
            focuscolor='',
            padx=25,
            pady=10,
            cursor='hand2'
        )
        draft_btn.pack(side=tk.BOTTOM, pady=(10, 0))
        
        # Position the window before showing content
        summary_popup.update_idletasks()  # Ensure window dimensions are calculated
        popup_width = summary_popup.winfo_width()
        popup_height = summary_popup.winfo_height()
        
        # Get mouse position and screen dimensions
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate x position ensuring window is fully visible
        x = min(max(mouse_x - popup_width//2, 0), screen_width - popup_width)
        
        # For y position, if mouse is in lower half of screen, position window above cursor
        if mouse_y > screen_height / 2:
            y = max(mouse_y - popup_height - 20, 0)  # Position above cursor with 20px gap
        else:
            y = min(mouse_y + 20, screen_height - popup_height)  # Position below cursor with 20px gap
        
        summary_popup.geometry(f"+{x}+{y}")
        summary_popup.deiconify()  # Show the window in its correct position
        
        def summarize(input_text):
            try:
                for output in self.summarizer.process(input_text):
                    self.root.after(0, lambda t=output: summary_label.config(text=t))
            except Exception as e:
                print(e)
            self.last_summary = output
        
        threading.Thread(target=lambda: summarize(text), daemon=True).start()

    def on_f10(self):
        # Show agent input window instead of copying text
        self.show_agent_input()

    def get_selected_text(self):
        # Copy selected text to clipboard
        with self.keyboard_controller.pressed(Key.cmd):
            self.keyboard_controller.tap('c')
        
        # Small delay to ensure clipboard is updated
        time.sleep(0.1)
        
        # Get text from clipboard
        return pyperclip.paste()

    def destroy_active_popups(self):
        # Destroy all active popups
        for popup in self.active_popups:
            try:
                popup.destroy()
            except:
                pass  # Popup might already be destroyed
        self.active_popups = []

    def show_draft_input(self, summary_x, summary_y, summary_width):
        draft_popup = tk.Toplevel(self.root)
        draft_popup.withdraw()  # Hide initially
        self.active_popups.append(draft_popup)
        draft_popup.title("Draft Reply")
        draft_popup.configure(bg='#f6f8fa')
        
        # Create frame for the three columns
        columns_frame = tk.Frame(draft_popup, bg='#f6f8fa')
        columns_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Calculate required height based on summary content
        num_lines = len(self.last_summary.split('\n'))
        line_height = max(num_lines * 1.5, 15)
        widget_height = min(line_height, 40) 
        
        # Column 1: Original Summary
        summary_frame = tk.Frame(
            columns_frame,
            bg='white',
            highlightbackground='#e1e4e8',
            highlightthickness=1,
            bd=0,
            relief=tk.FLAT
        )
        summary_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(summary_frame, text="Original Summary", bg='white', fg='#24292e', font=('Segoe UI', 12)).pack(padx=15, pady=(12,0), anchor='w')
        summary_text = tk.Text(
            summary_frame, 
            height=widget_height, 
            width=30, 
            wrap=tk.WORD,
            borderwidth=0,  # Remove border
            highlightthickness=0,  # Remove highlight border
            selectbackground='#e1e4e8',  # Very subtle selection color
            selectforeground='#24292e'  # Keep text readable when selected
        )
        summary_text.pack(fill='both', expand=True, padx=15, pady=12)
        summary_text.insert("1.0", self.last_summary)
        summary_text.config(state='disabled', bg='white', fg='#586069', font=('Segoe UI', 12))
        
        # Column 2: Draft Input
        input_frame = tk.Frame(
            columns_frame,
            bg='white',
            highlightbackground='#e1e4e8',
            highlightthickness=1,
            bd=0,
            relief=tk.FLAT
        )
        input_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(input_frame, text="Your Reply", bg='white', fg='#24292e', font=('Segoe UI', 12)).pack(padx=15, pady=(12,0), anchor='w')
        text_input = tk.Text(
            input_frame, 
            height=widget_height, 
            width=30, 
            wrap=tk.WORD,
            borderwidth=0,  # Remove border
            highlightthickness=0,  # Remove highlight border
            selectbackground='#e1e4e8',  # Very subtle selection color
            selectforeground='#24292e'  # Keep text readable when selected
        )
        text_input.pack(fill='both', expand=True, padx=15, pady=12)
        text_input.config(bg='white', fg='#24292e', font=('Segoe UI', 12))
        
        # Column 3: Improved Text
        improved_frame = tk.Frame(
            columns_frame,
            bg='white',
            highlightbackground='#e1e4e8',
            highlightthickness=1,
            bd=0,
            relief=tk.FLAT
        )
        improved_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(improved_frame, text="Improved Reply", bg='white', fg='#24292e', font=('Segoe UI', 12)).pack(padx=15, pady=(12,0), anchor='w')
        improved_text = tk.Text(
            improved_frame, 
            height=widget_height, 
            width=30, 
            wrap=tk.WORD,
            borderwidth=0,  # Remove border
            highlightthickness=0,  # Remove highlight border
            selectbackground='#e1e4e8',  # Very subtle selection color
            selectforeground='#24292e'  # Keep text readable when selected
        )
        improved_text.pack(fill='both', expand=True, padx=15, pady=12)
        improved_text.config(state='disabled', bg='white', fg='#586069', font=('Segoe UI', 12))
        
        # Add Copy button using tkmacosx
        copy_btn = Button(
            improved_frame, 
            text="Copy",
            command=lambda: pyperclip.copy(improved_text.get("1.0", "end-1c")),
            font=('Segoe UI', 14),
            bg='#0066FF',
            fg='white',
            activebackground='#0052CC',
            activeforeground='white',
            borderless=True,
            focuscolor='',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        copy_btn.pack(pady=(0, 12))
        
        # Add "Smol Improvement?" button using tkmacosx
        improve_btn = Button(
            input_frame, 
            text="Smol Improvement?",
            command=lambda: self.generate_improved_text(
                text_input.get("1.0", "end-1c"),
                improved_text),
            font=('Segoe UI', 14),
            bg='#0066FF',
            fg='white',
            activebackground='#0052CC',
            activeforeground='white',
            borderless=True,
            focuscolor='',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        improve_btn.pack(pady=(0, 12))
        
        # Position window relative to the summary window's position
        draft_popup.update_idletasks()
        screen_width = draft_popup.winfo_screenwidth()
        screen_height = draft_popup.winfo_screenheight()
        popup_width = draft_popup.winfo_width()
        if popup_width == 1:
            popup_width = 800
        popup_height = draft_popup.winfo_height()
        
        # Calculate center point of the summary window
        summary_center_x = summary_x + summary_width//2
        
        # Center the new window on the same point, but ensure it stays on screen
        new_x = max(min(max(summary_center_x - popup_width//2, 0), screen_width - popup_width), 0)
        # Position vertically based on screen space available
        if summary_y > screen_height / 2:
            new_y = max(summary_y - popup_height - 10, 0)  # 10px gap above summary
        else:
            new_y = min(summary_y + 10, screen_height - popup_height)  # 10px gap below summary
        
        draft_popup.geometry(f"+{new_x}+{new_y}")
        draft_popup.deiconify()  # Show in correct position

    def generate_improved_text(self, text, improved_text_widget):
        # Get reference to the improve button
        improve_btn = improved_text_widget.master.master.children['!frame2'].children['!button']
        
        # Disable the button and change text to show processing
        improve_btn.configure(
            state='disabled',
            text="Generating...",
            bg='#A8A8A8',  # Grayed out color
        )
        
        # Update the improve function
        improved_text_widget.config(state='normal')
        improved_text_widget.delete("1.0", tk.END)
        improved_text_widget.insert("1.0", "Generating improvement...")
        improved_text_widget.config(state='disabled')
        
        def improve(input_text):
            try:
                for output in self.rewriter.process(input_text):
                    self.root.after(0, lambda t=output: self.update_improved_text(improved_text_widget, t))
                
                # Re-enable button and restore original state after generation is complete
                self.root.after(0, lambda: improve_btn.config(
                    state='normal',
                    text="Smol Improvement?",
                    bg='#0066FF'  # Restore original color
                ))
            except Exception as e:
                # Make sure to re-enable button even if there's an error
                self.root.after(0, lambda: improve_btn.config(
                    state='normal',
                    text="Smol Improvement?",
                    bg='#0066FF'
                ))
                raise e
        
        threading.Thread(target=lambda: improve(text), daemon=True).start()

    def update_improved_text(self, text_widget, new_text):
        text_widget.config(state='normal')
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", new_text)
        text_widget.config(state='disabled')

    def show_agent_input(self):
        # Create new popup for agent input
        agent_popup = tk.Toplevel(self.root)
        self.active_popups.append(agent_popup)
        agent_popup.title("SmolAgent")
        
        # Create input area
        input_frame = tk.Frame(agent_popup)
        input_frame.pack(padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(input_frame, text="What would you like me to do?").pack()
        text_input = tk.Text(input_frame, height=4, width=50, wrap=tk.WORD)
        text_input.pack(pady=5)
        
        # Create output area
        output_frame = tk.Frame(agent_popup)
        output_frame.pack(padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(output_frame, text="Response:").pack()
        output_text = tk.Text(output_frame, height=8, width=50, wrap=tk.WORD)
        output_text.pack(pady=5)
        output_text.config(state='disabled')
        
        def process_agent_request():
            query = text_input.get("1.0", "end-1c")
            output_text.config(state='normal')
            output_text.delete("1.0", tk.END)
            output_text.insert("1.0", "Processing request...\n")
            output_text.config(state='disabled')
            
            def run_agent():
                full_response = []
                for response in self.agent.process(query):
                    full_response.append(response)
                    self.root.after(0, lambda t="\n".join(full_response): self.update_agent_output(output_text, t))
            
            threading.Thread(target=run_agent, daemon=True).start()
        
        # Add Submit button
        submit_btn = tk.Button(agent_popup, text="Submit", command=process_agent_request)
        submit_btn.pack(pady=5)
        
        # Position window
        agent_popup.update_idletasks()
        screen_width = agent_popup.winfo_screenwidth()
        screen_height = agent_popup.winfo_screenheight()
        popup_width = agent_popup.winfo_width()
        popup_height = agent_popup.winfo_height()
        x = (screen_width - popup_width) // 2
        y = (screen_height - popup_height) // 2
        agent_popup.geometry(f"+{x}+{y}")

    def update_agent_output(self, text_widget, new_text):
        text_widget.config(state='normal')
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", new_text)
        text_widget.config(state='disabled')

    def show_chat_window(self):
        chat_window = tk.Toplevel(self.root)
        self.active_popups.append(chat_window)
        chat_window.title("SmolChat")
        
        # Configure the chat window to be resizable
        chat_window.geometry("800x800")
        chat_window.minsize(600, 600)
        
        # Create split view with history panel
        history_panel = tk.Frame(chat_window, width=200, padx=5, pady=10)
        history_panel.pack(side=tk.LEFT, fill=tk.Y)
        history_panel.pack_propagate(False)  # Maintain width
        
        # Create main chat area
        main_frame = tk.Frame(chat_window, padx=10, pady=10)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create chat display first
        chat_display = tk.Text(main_frame, wrap=tk.WORD)
        chat_display.pack(fill=tk.BOTH, expand=True)
        chat_display.config(state='disabled')
        
        # Add input field and send button
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        chat_input = tk.Text(input_frame, height=3, wrap=tk.WORD)
        chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        send_btn = tk.Button(input_frame, text="Send", 
                           command=lambda: self.process_chat_message(
                               chat_input.get("1.0", "end-1c").strip(),
                               chat_display))
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bind Enter key to send message
        chat_input.bind("<Return>", lambda e: [
            self.process_chat_message(
                chat_input.get("1.0", "end-1c").strip(),
                chat_display),
            "break"  # Prevent the default newline behavior
        ][1])
        
        # Now add the New Chat button (after chat_display is created)
        new_chat_btn = tk.Button(history_panel, text="New Chat", 
                               command=lambda: self.start_new_chat(chat_display))
        new_chat_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Add listbox for chat history
        history_label = tk.Label(history_panel, text="Previous Chats")
        history_label.pack()
        chat_listbox = tk.Listbox(history_panel, height=20)
        chat_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Get and sort chats by modification time (newest first)
        saved_chats = self.chatter.get_saved_chats()
        sorted_chats = sorted(
            saved_chats,
            key=lambda x: os.path.getmtime(os.path.join("saved_chats", f"chat_{x}.json")),
            reverse=True
        )
        
        # Populate chat history with sorted chats
        for chat_id in sorted_chats:
            chat_listbox.insert(tk.END, chat_id)
        
        # Bind selection event
        chat_listbox.bind('<<ListboxSelect>>', 
                         lambda e: self.load_selected_chat(chat_listbox, chat_display))
        
        # Add scrollbar to listbox
        history_scrollbar = tk.Scrollbar(history_panel, command=chat_listbox.yview)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        chat_listbox.config(yscrollcommand=history_scrollbar.set)
        
        # Store references to UI elements that need to be disabled during chat
        self.chat_controls = {
            'listbox': chat_listbox,
            'new_chat_btn': new_chat_btn
        }

        # Add text tags with softer colors
        chat_display.tag_configure("assistant_name", foreground="#E57373")  # Soft red
        chat_display.tag_configure("user_name", foreground="#7986CB")      # Soft blue

    def load_selected_chat(self, listbox: tk.Listbox, chat_display: tk.Text):
        selection = listbox.curselection()
        if selection:
            chat_id = listbox.get(selection[0])
            self.chatter.load_chat(chat_id)
            self.display_chat_history(chat_display)

    def start_new_chat(self, chat_display):
        # Only save the current chat if it has been modified since loading
        if self.chatter.has_current_chat() and self.chatter.is_chat_modified():
            # Get full chat history as a single string
            chat_history = "\n".join([f"{msg.role}: {msg.content}" 
                                    for msg in self.chatter.get_chat_history()])
            
            # If we're continuing an existing chat, use its ID
            current_chat_id = self.chatter.get_current_chat_id()
            if current_chat_id:
                # Save using existing ID
                self.chatter.save_current_chat(current_chat_id, overwrite=True)
            else:
                # Generate new title for new chat
                summary = ""
                for chunk in self.titler.process(chat_history):
                    summary = chunk
                
                summary_title = summary[:50].strip().replace("/", "-").replace("\\", "-")
                self.chatter.save_current_chat(summary_title, overwrite=True)
        
        # Start new chat
        self.chatter.start_new_chat()
        
        # Clear and update display
        self.display_chat_history(chat_display)
        
        # Update the chat history listbox with sorted chats
        listbox = self.chat_controls['listbox']
        listbox.delete(0, tk.END)
        saved_chats = self.chatter.get_saved_chats()
        sorted_chats = sorted(
            saved_chats,
            key=lambda x: os.path.getmtime(os.path.join("saved_chats", f"chat_{x}.json")),
            reverse=True
        )
        for chat_id in sorted_chats:
            listbox.insert(tk.END, chat_id)

    def process_chat_message(self, message: str, chat_display: tk.Text):
        if not message.strip():  # Skip empty messages
            return
            
        # Disable chat controls while processing
        self.chat_controls['listbox'].config(state='disabled')
        self.chat_controls['new_chat_btn'].config(state='disabled')
            
        chat_display.config(state='normal')
        
        # Add extra newline before user message for spacing
        chat_display.insert(tk.END, "")  # Start new line
        chat_display.insert(tk.END, self.username, "user_name")  # Add colored username
        chat_display.insert(tk.END, f": {message}\n")  # Add message
        
        chat_display.insert(tk.END, "\n")  # Add spacing
        chat_display.insert(tk.END, self.chatter.name, "assistant_name")  # Add colored AI name
        chat_display.insert(tk.END, ": ")  # Add separator
        
        # Clear the input field (get its reference from chat_display's master)
        input_frame = chat_display.master.children['!frame']
        chat_input = input_frame.children['!text']
        chat_input.delete("1.0", tk.END)
        
        # Initialize an empty string to store the full response
        self.current_response = ""
        
        chat_display.see(tk.END)
        chat_display.config(state='disabled')
        
        def chat_response():
            try:
                for chunk in self.chatter.process(message):
                    # Only send the new part of the response
                    if chunk.startswith(self.current_response):
                        new_text = chunk[len(self.current_response):]
                        if new_text:  # Only update if there's new text
                            self.current_response = chunk
                            self.root.after(0, lambda t=new_text: self.update_chat_display(chat_display, t))
                self.root.after(0, lambda t="\n\n": self.update_chat_display(chat_display, t))
            finally:
                # Re-enable chat controls after response is complete
                self.root.after(0, self.enable_chat_controls)
        
        threading.Thread(target=chat_response, daemon=True).start()

    def enable_chat_controls(self):
        """Re-enable chat controls after response is complete"""
        self.chat_controls['listbox'].config(state='normal')
        self.chat_controls['new_chat_btn'].config(state='normal')

    def update_chat_display(self, chat_display: tk.Text, new_text: str):
        chat_display.config(state='normal')
        chat_display.insert(tk.END, new_text)
        chat_display.see(tk.END)
        chat_display.config(state='disabled')

    def display_chat_history(self, chat_display: tk.Text):
        chat_display.config(state='normal')
        chat_display.delete("1.0", tk.END)
        
        # Configure text tags with softer colors
        chat_display.tag_configure("assistant_name", foreground="#E57373")  # Soft red
        chat_display.tag_configure("user_name", foreground="#7986CB")      # Soft blue
        
        for message in self.chatter.get_chat_history():
            if message.role == "user":
                chat_display.insert(tk.END, "\n")  # Add spacing
                chat_display.insert(tk.END, self.username, "user_name")  # Change "You" to username
                chat_display.insert(tk.END, f": {message.content}\n")
            else:
                chat_display.insert(tk.END, "\n")  # Add spacing
                chat_display.insert(tk.END, self.chatter.name, "assistant_name")
                chat_display.insert(tk.END, f": {message.content}\n")
        
        chat_display.config(state='disabled')
        chat_display.see(tk.END)

# Run the app
root = tk.Tk()

# Set default font size for all tkinter widgets
default_font = ('Segoe UI', 14)  # Changed from TkDefaultFont to Segoe UI
root.option_add("*Font", default_font)
root.option_add("*Entry.Font", default_font)
root.option_add("*Text.Font", default_font)
root.option_add("*Button.Font", default_font)
root.option_add("*Label.Font", default_font)

app = TextPopupApp(root)
root.mainloop()
