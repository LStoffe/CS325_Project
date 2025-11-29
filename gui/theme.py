
import tkinter as tk
from tkinter import ttk

def apply_dark_theme(root):
    style = ttk.Style(root)
    root.configure(bg='#1e1e1e')
    style.theme_use('clam')
    style.configure('.', background='#1e1e1e', foreground='white', fieldbackground='#2e2e2e')
    style.configure('TButton', background='#3a3a3a', foreground='white')
    style.configure('TLabel', background='#1e1e1e', foreground='white')
    style.configure('TEntry', fieldbackground='#2e2e2e')
