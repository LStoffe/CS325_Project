
import tkinter as tk
from tkinter import ttk
import webbrowser

class ResultsPopup:
    def __init__(self, parent, df):
        self.win=tk.Toplevel(parent)
        self.win.title("Top 10 Matching Jobs")
        self.win.geometry("1100x700")
        self.win.configure(bg="#1e1e1e")

        container=ttk.Frame(self.win)
        container.pack(fill="both", expand=True)

        canvas=tk.Canvas(container, bg="#1e1e1e")
        scrollbar=ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll=ttk.Frame(canvas)

        scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers=["Title","Company","Location","Score","Link"]
        for c,h in enumerate(headers):
            ttk.Label(scroll, text=h).grid(row=0,column=c,padx=10,pady=10)

        for i,(idx,row) in enumerate(df.iterrows(), start=1):
            ttk.Label(scroll, text=row["title"]).grid(row=i,column=0,padx=10,pady=5)
            ttk.Label(scroll, text=row.get("company","")).grid(row=i,column=1,padx=10,pady=5)
            ttk.Label(scroll, text=row.get("location","")).grid(row=i,column=2,padx=10,pady=5)
            ttk.Label(scroll, text=f"{row['score']:.4f}").grid(row=i,column=3,padx=10,pady=5)

            url=row.get("redirect_url","")
            ttk.Button(scroll, text="Open", command=lambda u=url: webbrowser.open(u)).grid(row=i,column=4,padx=10,pady=5)
