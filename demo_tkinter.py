import tkinter as tk
import time
import threading
import queue
from pynput import keyboard
from smol_tools.summarizer import SmolSummarizer
from smol_tools.rewriter import SmolRewriter
from pynput.keyboard import Key, Controller
import pyperclip
from smol_tools.agent import SmolToolAgent

class TextPopupApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Start with the window hidden
        self.text_queue = queue.Queue()
        self.last_text = ""
        self.active_popups = []
        self.last_summary = ""
        
        # Initialize tools
        self.summarizer = SmolSummarizer()
        self.rewriter = SmolRewriter()
        self.agent = SmolToolAgent()
        
        self.keyboard_controller = Controller()
        
        # Replace the keyboard listener with GlobalHotKeys
        self.keyboard_listener = keyboard.GlobalHotKeys({
            "<F9>": self.on_f9,
            "<F10>": self.on_f10,
            "<ctrl>+s": self.on_f10 
        })
        self.keyboard_listener.start()
        
        # Start processing the queue in the main thread
        self.process_queue()

    def on_f9(self):
        selected_text = self.get_selected_text()
        if selected_text:
            self.text_queue.put(selected_text)

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

    def process_queue(self):
        try:
            # Check if there's new text to display
            text = self.text_queue.get_nowait()
            self.show_popup(text)
        except queue.Empty:
            pass
        # Schedule the next check
        self.root.after(100, self.process_queue)

    def destroy_active_popups(self):
        # Destroy all active popups
        for popup in self.active_popups:
            try:
                popup.destroy()
            except:
                pass  # Popup might already be destroyed
        self.active_popups = []

    def show_popup(self, text):
        # Clear any existing popups
        self.destroy_active_popups()
        
        self.popup = tk.Toplevel(self.root)
        self.active_popups.append(self.popup)  # Track this popup
        self.popup.title("Summarize?")
        
        # Add preview of text (first 100 characters)
        preview = text[:100] + "..." if len(text) > 100 else text
        preview_label = tk.Label(self.popup, text=preview, wraplength=300)
        preview_label.pack(padx=10, pady=5)
        
        # Create button frame
        button_frame = tk.Frame(self.popup)
        button_frame.pack(pady=5)
        
        # Add Summarize button
        summarize_btn = tk.Button(button_frame, text="Smol summary?", command=lambda: self.generate_summary(text))
        summarize_btn.pack(side=tk.LEFT, padx=5)
        
        # Add Close button
        close_btn = tk.Button(button_frame, text="Close", command=self.popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)
        
        # Position window
        self.popup.update_idletasks()
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        popup_width = self.popup.winfo_width()
        popup_height = self.popup.winfo_height()
        self.popup_position = (mouse_x-popup_width//2, mouse_y-popup_height//2)  # Store position
        self.popup.geometry(f"+{self.popup_position[0]}+{self.popup_position[1]}")
        
        self.popup.lift()
        self.popup.attributes('-topmost', True)

    def generate_summary(self, text):
        popup_position = self.popup_position  # Store position before destroying
        self.popup.destroy()  # Close the initial popup
        
        # Create a new popup for the summary
        summary_popup = tk.Toplevel(self.root)
        self.active_popups.append(summary_popup)  # Track this popup
        summary_popup.title("Summary")
        
        # Create summary label right away
        summary_label = tk.Label(summary_popup, text="Generating summary...", wraplength=300)
        summary_label.pack(padx=10, pady=10)
        
        # Position the summary popup at the same location as the original
        summary_popup.geometry(f"+{popup_position[0]}+{popup_position[1]}")
        
        def summarize(input_text):
            for output in self.summarizer.process(input_text):
                self.root.after(0, lambda t=output: summary_label.config(text=t))
            self.last_summary = output
            summary_popup.after(0, lambda: self.finalize_summary_popup(summary_popup))
        
        # Pass the text parameter to summarize
        threading.Thread(target=lambda: summarize(text), daemon=True).start()

    def finalize_summary_popup(self, popup):
        # Position window
        popup.update_idletasks()
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()
        popup.geometry(f"+{mouse_x-popup_width//2}+{mouse_y-popup_height//2}")
        
        # Add "Draft Reply?" button
        draft_btn = tk.Button(popup, text="Draft Reply?", 
                             command=lambda: [
                                 self.show_draft_input(popup.winfo_x(), popup.winfo_y()),
                                 popup.destroy()  # Close the summary window
                             ])
        draft_btn.pack(pady=5)
        
        # Auto-close after 10 seconds (optional now)
        # popup.after(10000, popup.destroy)

    def show_draft_input(self, x, y):
        # Create new popup for draft input
        draft_popup = tk.Toplevel(self.root)
        self.active_popups.append(draft_popup)
        draft_popup.title("Draft Reply")
        
        # Create frame for the three columns
        columns_frame = tk.Frame(draft_popup)
        columns_frame.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Calculate required height based on summary content
        # Each line is roughly 20-25 pixels, add some padding
        num_lines = len(self.last_summary.split('\n'))
        line_height = max(num_lines * 1.5, 10)  # Minimum 10 lines, multiply by 1.5 for comfort
        widget_height = min(line_height, 20)  # Maximum 20 lines
        
        # Column 1: Original Summary
        summary_frame = tk.Frame(columns_frame)
        summary_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(summary_frame, text="Original Summary", wraplength=300).pack()
        summary_text = tk.Text(summary_frame, height=widget_height, width=30, wrap=tk.WORD)
        summary_text.pack(fill='both', expand=True)
        summary_text.insert("1.0", self.last_summary)
        summary_text.config(state='disabled')
        
        # Column 2: Draft Input
        input_frame = tk.Frame(columns_frame)
        input_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(input_frame, text="Your Reply").pack()
        text_input = tk.Text(input_frame, height=widget_height, width=30, wrap=tk.WORD)
        text_input.pack(fill='both', expand=True)
        
        # Column 3: Improved Text
        improved_frame = tk.Frame(columns_frame)
        improved_frame.pack(side=tk.LEFT, padx=5, fill='both', expand=True)
        tk.Label(improved_frame, text="Improved Reply").pack()
        improved_text = tk.Text(improved_frame, height=widget_height, width=30, wrap=tk.WORD)
        improved_text.pack(fill='both', expand=True)
        improved_text.config(state='disabled')
        
        # Add "Smol Improvement?" button below the middle column
        improve_btn = tk.Button(input_frame, text="Smol Improvement?", 
                              command=lambda: self.generate_improved_text(
                                  text_input.get("1.0", "end-1c"), 
                                  improved_text))
        improve_btn.pack(pady=5)
        
        # Position window
        draft_popup.update_idletasks()
        screen_width = draft_popup.winfo_screenwidth()
        screen_height = draft_popup.winfo_screenheight()
        popup_width = draft_popup.winfo_width()
        popup_height = draft_popup.winfo_height()
        x = (screen_width - popup_width) // 2
        y = (screen_height - popup_height) // 2
        draft_popup.geometry(f"+{x}+{y}")

    def generate_improved_text(self, text, improved_text_widget):
        # Update the improve function
        improved_text_widget.config(state='normal')
        improved_text_widget.delete("1.0", tk.END)
        improved_text_widget.insert("1.0", "Generating improvement...")
        improved_text_widget.config(state='disabled')
        
        def improve(input_text):
            for output in self.rewriter.process(input_text):
                self.root.after(0, lambda t=output: self.update_improved_text(improved_text_widget, t))
        
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

# Run the app
root = tk.Tk()
app = TextPopupApp(root)
root.mainloop()
